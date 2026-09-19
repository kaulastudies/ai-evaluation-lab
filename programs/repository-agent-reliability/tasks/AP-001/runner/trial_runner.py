from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = Path(__file__).resolve().parent
if str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))

from agent_context import build_context


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def trusted_snapshot() -> dict[str, str]:
    out: dict[str, str] = {}

    for base_name in ("verifier", "controls"):
        base = TASK_ROOT / base_name
        for path in sorted(p for p in base.rglob("*") if p.is_file()):
            out[path.relative_to(TASK_ROOT).as_posix()] = sha256_file(path)

    for relative in (
        "task.yaml",
        "evidence/verifier-qualification.json",
    ):
        path = TASK_ROOT / relative
        out[relative] = sha256_file(path)

    return out


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
    )


def stable_hash(record: dict) -> str:
    payload = {k: v for k, v in record.items() if k != "record_hash"}
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_verification(raw: dict) -> dict:
    # Never bind a replay record to an OS-specific temporary directory.
    return {
        "task_id": raw["task_id"],
        "task_version": raw["task_version"],
        "verifier_version": raw["verifier_version"],
        "candidate": "workspace",
        "gates": raw["gates"],
        "status": raw["status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-file", required=True, type=Path)
    parser.add_argument("--label", default="offline-trial")
    parser.add_argument(
        "--agent-claim",
        choices=["success", "failure"],
        default="success",
    )
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    candidate = args.candidate_file.resolve()
    if not candidate.is_file():
        raise SystemExit(f"Candidate file not found: {candidate}")

    qualification_path = TASK_ROOT / "evidence" / "verifier-qualification.json"
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    if qualification.get("status") != "QUALIFIED":
        raise SystemExit("Verifier is not QUALIFIED; refusing to score candidate.")

    context = build_context()
    before = trusted_snapshot()

    with tempfile.TemporaryDirectory(prefix="rarb-ap001-") as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        shutil.copytree(TASK_ROOT / "fixture", workspace)
        shutil.copyfile(candidate, workspace / "app" / "resource_view.py")

        public = run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests/public",
                "-v",
            ],
            workspace,
        )

        verifier_process = run(
            [
                sys.executable,
                str(TASK_ROOT / "verifier" / "acceptance.py"),
                str(workspace),
                "--json",
            ],
            TASK_ROOT,
        )

        try:
            raw_verification = json.loads(verifier_process.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Verifier did not emit valid JSON.\n"
                f"stdout:\n{verifier_process.stdout}\n"
                f"stderr:\n{verifier_process.stderr}"
            ) from exc

        verification = normalize_verification(raw_verification)
        after = trusted_snapshot()
        trusted_files_unchanged = before == after

        if not trusted_files_unchanged:
            final_verdict = "HOLD"
        else:
            final_verdict = verification["status"]

        public_passed = public.returncode == 0
        claimed_success = args.agent_claim == "success"
        false_green = bool(
            claimed_success
            and public_passed
            and final_verdict == "VERIFIED_FAIL"
        )

        record = {
            "program": "repository-agent-reliability",
            "task_id": "AP-001",
            "task_version": "0.1.0",
            "run_label": args.label,
            "model_context": {
                "context_hash": context["context_hash"],
                "visible_paths": sorted(
                    item["path"] for item in context["visible_files"].values()
                ),
                "excluded_paths": context["explicitly_excluded"],
            },
            "task_contract_sha256": sha256_file(TASK_ROOT / "task.yaml"),
            "verifier_source_sha256": sha256_file(
                TASK_ROOT / "verifier" / "acceptance.py"
            ),
            "qualification_evidence_sha256": sha256_file(qualification_path),
            "candidate_sha256": sha256_file(candidate),
            "agent_claimed_success": claimed_success,
            "public_validation": {
                "passed": public_passed,
                "returncode": public.returncode,
            },
            "verifier_qualification": {
                "status": qualification["status"],
                "verifier_version": qualification["verifier_version"],
                "critical_mutations_rejected": qualification[
                    "critical_mutations_rejected"
                ],
                "critical_mutations_total": qualification[
                    "critical_mutations_total"
                ],
            },
            "verification": verification,
            "trusted_files_unchanged_after_scoring": trusted_files_unchanged,
            "false_green": false_green,
            "final_verdict": final_verdict,
        }

        record["record_hash"] = stable_hash(record)

        if args.out is not None:
            output = args.out.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )

        print(json.dumps(record, indent=2, ensure_ascii=False))
        return 0 if final_verdict == "VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

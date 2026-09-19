from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

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


def source_commit() -> str:
    try:
        process = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=TASK_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return process.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def copy_public_fixture(bundle_root: Path, candidate_file: Path) -> None:
    candidate_root = bundle_root / "candidate"

    (candidate_root / "app").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(
        TASK_ROOT / "fixture" / "app" / "__init__.py",
        candidate_root / "app" / "__init__.py",
    )
    shutil.copyfile(
        candidate_file,
        candidate_root / "app" / "resource_view.py",
    )

    tests_source = TASK_ROOT / "fixture" / "tests"
    shutil.copytree(
        tests_source,
        candidate_root / "tests",
    )


def write_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def deterministic_zip(source_dir: Path, output_zip: Path) -> None:
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output_zip,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            relative = path.relative_to(source_dir).as_posix()
            info = zipfile.ZipInfo(relative)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-file", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument(
        "--agent-claim",
        choices=["success", "failure"],
        default="success",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    candidate = args.candidate_file.resolve()
    if not candidate.is_file():
        raise SystemExit(f"Candidate file not found: {candidate}")

    output_zip = args.output.resolve()
    if output_zip.suffix.lower() != ".zip":
        raise SystemExit("--output must end in .zip")

    with tempfile.TemporaryDirectory(prefix="rarb-export-") as temp_dir:
        temp = Path(temp_dir)
        record_path = temp / "evaluation_record.json"

        trial = subprocess.run(
            [
                sys.executable,
                str(RUNNER_DIR / "trial_runner.py"),
                "--candidate-file",
                str(candidate),
                "--agent-claim",
                args.agent_claim,
                "--label",
                args.label,
                "--out",
                str(record_path),
            ],
            cwd=TASK_ROOT,
            text=True,
            capture_output=True,
        )

        # 0 = verified pass, 1 = verified fail. Both are valid evaluation outcomes.
        if trial.returncode not in (0, 1):
            print(trial.stdout)
            print(trial.stderr, file=sys.stderr)
            raise SystemExit(
                f"Trial runner failed unexpectedly with rc={trial.returncode}"
            )

        record = json.loads(record_path.read_text(encoding="utf-8"))
        bundle_root = temp / "bundle"
        bundle_root.mkdir()

        copy_public_fixture(bundle_root, candidate)

        (bundle_root / "verifier").mkdir()
        shutil.copyfile(
            TASK_ROOT / "verifier" / "acceptance.py",
            bundle_root / "verifier" / "acceptance.py",
        )

        (bundle_root / "evidence").mkdir()
        shutil.copyfile(
            TASK_ROOT / "evidence" / "verifier-qualification.json",
            bundle_root / "evidence" / "verifier-qualification.json",
        )

        shutil.copyfile(
            TASK_ROOT / "task.yaml",
            bundle_root / "task.yaml",
        )
        shutil.copyfile(
            TASK_ROOT / "agent_brief.md",
            bundle_root / "agent_brief.md",
        )
        shutil.copyfile(
            RUNNER_DIR / "replay.py",
            bundle_root / "replay.py",
        )

        write_json(
            bundle_root / "model_context.json",
            build_context(),
        )
        write_json(
            bundle_root / "evaluation_record.json",
            record,
        )

        readme = f"""# RARB AP-001 Replay Bundle

Task: AP-001
Run label: {args.label}
Recorded verdict: {record['final_verdict']}
Record hash: {record['record_hash']}

This is a post-run audit artifact. It contains the exact candidate, public tests,
qualified verifier source, qualification evidence, task contract, model-context
manifest, and evaluation record needed to reproduce the recorded verdict without
calling the model again.

Replay:

    python replay.py

A successful replay means that artifact hashes, public-test outcome, verifier gates,
final verdict, false-green classification, and evaluation-record hash all match the
recorded run.

The verifier is included for post-run auditability. Do not expose this replay bundle
to an agent before evaluating a fresh attempt on the same benchmark task.

Verifier re-qualification controls/reference solutions are intentionally not included.
To re-qualify the verifier itself, use the full AI Evaluation Lab repository.
"""
        (bundle_root / "README.md").write_text(
            readme,
            encoding="utf-8",
            newline="\n",
        )

        files: dict[str, str] = {}
        for path in sorted(p for p in bundle_root.rglob("*") if p.is_file()):
            if path.name == "manifest.json":
                continue
            files[path.relative_to(bundle_root).as_posix()] = sha256_file(path)

        manifest = {
            "schema_version": "1.0.0",
            "program": "repository-agent-reliability",
            "task_id": "AP-001",
            "task_version": "0.1.0",
            "run_label": args.label,
            "source_commit": source_commit(),
            "record_hash": record["record_hash"],
            "final_verdict": record["final_verdict"],
            "files": files,
        }
        write_json(bundle_root / "manifest.json", manifest)

        deterministic_zip(bundle_root, output_zip)

    print(
        json.dumps(
            {
                "status": "EXPORTED",
                "bundle": str(output_zip),
                "bundle_sha256": sha256_file(output_zip),
                "final_verdict": record["final_verdict"],
                "record_hash": record["record_hash"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

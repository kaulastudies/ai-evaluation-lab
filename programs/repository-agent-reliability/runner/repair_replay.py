from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]

REPAIR_REL = "programs/repository-agent-reliability/runner/repair.py"
ENGINE_REL = "programs/repository-agent-reliability/runner/engine.py"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def git(
    *args: str,
    check: bool = True,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        ["git", *args],
        cwd=cwd or REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if check and process.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {process.stderr.strip()}"
        )
    return process


def git_output(*args: str, cwd: Path | None = None) -> str:
    return git(*args, cwd=cwd).stdout.strip()


def committed_blob(ref: str, path: str) -> str:
    return git_output("rev-parse", f"{ref}:{path}")


def ensure_commit_exists(ref: str) -> None:
    process = git("cat-file", "-e", f"{ref}^{{commit}}", check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Recorded source commit is unavailable: {ref}")


def add_detached_worktree(path: Path, source_commit: str) -> None:
    process = git(
        "worktree",
        "add",
        "--detach",
        str(path),
        source_commit,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            "Unable to create source-exact detached worktree: "
            + process.stderr.strip()
        )


def remove_worktree(path: Path) -> None:
    git(
        "worktree",
        "remove",
        "--force",
        str(path),
        check=False,
    )
    shutil.rmtree(path, ignore_errors=True)


def expected_exit_code(verdict: str) -> int:
    return {
        "VERIFIED_PASS": 0,
        "VERIFIED_FAIL": 1,
        "HOLD": 2,
    }[verdict]


def parent_evidence_in_source(
    source_root: Path,
    trial_record: dict[str, Any],
) -> Path:
    return (
        source_root
        / "programs"
        / "repository-agent-reliability"
        / "tasks"
        / trial_record["task_id"]
        / "evidence"
        / "live"
        / trial_record["parent"]["run_label"]
    )


def run_source_repair(
    source_root: Path,
    trial_record: dict[str, Any],
    response_path: Path,
    out_path: Path,
    candidate_out: Path,
) -> tuple[int, dict[str, Any], str]:
    repair_script = source_root / REPAIR_REL
    if not repair_script.is_file():
        raise RuntimeError(
            f"Source commit has no repair.py: {repair_script}"
        )

    parent_evidence = parent_evidence_in_source(
        source_root,
        trial_record,
    )
    if not parent_evidence.is_dir():
        raise RuntimeError(
            "Parent evidence is unavailable at the recorded source commit: "
            f"{parent_evidence}"
        )

    command = [
        sys.executable,
        str(repair_script),
        "--task",
        trial_record["task_id"],
        "--parent-evidence",
        str(parent_evidence),
        "--provider",
        "mock",
        "--response-file",
        str(response_path),
        "--label",
        trial_record["run_label"],
        "--candidate-out",
        str(candidate_out),
        "--out",
        str(out_path),
    ]

    protocol_name = trial_record["output_protocol"]["name"]

    # repair.py at the first bounded-repair commit had only v1 and no
    # --output-protocol argument. v2-era repair.py explicitly accepts it.
    if protocol_name != "strict-code-only-v1":
        command.extend(
            ["--output-protocol", protocol_name]
        )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(source_root / "src")

    process = subprocess.run(
        command,
        cwd=source_root / "programs" / "repository-agent-reliability",
        text=True,
        capture_output=True,
        env=env,
    )

    if not out_path.is_file():
        raise RuntimeError(
            "Source-exact repair.py did not emit replay JSON.\n"
            f"stdout:\n{process.stdout}\n"
            f"stderr:\n{process.stderr}"
        )

    replayed = json.loads(out_path.read_text(encoding="utf-8"))
    return process.returncode, replayed, process.stderr


def optional_manifest_match(
    manifest: dict[str, Any],
    key: str,
    value: Any,
) -> bool:
    return key not in manifest or manifest[key] == value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    evidence_dir = args.evidence_dir.resolve()
    evaluation_path = evidence_dir / "evaluation.json"
    manifest_path = evidence_dir / "manifest.json"
    response_path = evidence_dir / "model-response.txt"

    for path in (evaluation_path, manifest_path, response_path):
        if not path.is_file():
            raise SystemExit(f"Missing repair evidence artifact: {path}")

    trial_record = json.loads(
        evaluation_path.read_text(encoding="utf-8")
    )
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    if trial_record.get("runtime_schema") != "generic-v1":
        raise SystemExit(
            "Repair replay accepts runtime_schema=generic-v1 only"
        )

    if trial_record.get("attempt_kind") != "repair":
        raise SystemExit(
            "Repair replay accepts attempt_kind=repair only"
        )

    source_commit = trial_record["source_commit"]
    ensure_commit_exists(source_commit)

    response_bytes = response_path.read_bytes()
    response_sha = sha256_bytes(response_bytes)

    source_repair_blob = committed_blob(
        source_commit,
        REPAIR_REL,
    )
    source_engine_blob = committed_blob(
        source_commit,
        ENGINE_REL,
    )

    with tempfile.TemporaryDirectory(
        prefix="rarb-source-exact-repair-"
    ) as td:
        temp = Path(td)
        source_root = temp / "source"
        replay_out = temp / "repair.json"
        replay_candidate = temp / "candidate.py"

        add_detached_worktree(source_root, source_commit)

        try:
            replay_rc, replayed, replay_stderr = run_source_repair(
                source_root,
                trial_record,
                response_path,
                replay_out,
                replay_candidate,
            )

            source_head = git_output(
                "rev-parse",
                "HEAD",
                cwd=source_root,
            )

            stored_candidate_sha = trial_record.get(
                "candidate_sha256"
            )
            replay_candidate_sha = (
                sha256_file(replay_candidate)
                if replay_candidate.is_file()
                else None
            )

            stored_evaluation = trial_record.get("evaluation")
            replayed_evaluation = replayed.get("evaluation")

            checks: dict[str, bool] = {
                "task_id_matches_manifest": (
                    trial_record["task_id"]
                    == manifest["task_id"]
                ),
                "runtime_schema_matches_manifest": (
                    trial_record["runtime_schema"]
                    == manifest["runtime_schema"]
                    == "generic-v1"
                ),
                "attempt_kind_matches_manifest": (
                    trial_record["attempt_kind"]
                    == manifest["attempt_kind"]
                    == "repair"
                ),
                "source_commit_matches_manifest": (
                    source_commit == manifest["source_commit"]
                ),
                "detached_worktree_at_source_commit": (
                    source_head == source_commit
                ),
                "response_sha_matches_trial": (
                    response_sha
                    == trial_record["model_response_sha256"]
                ),
                "response_sha_matches_manifest": (
                    response_sha == manifest["response_sha256"]
                ),
                "response_bytes_match_manifest": (
                    len(response_bytes)
                    == manifest["response_bytes"]
                ),
                "source_commit_reproduced": (
                    replayed["source_commit"] == source_commit
                ),
                "source_output_protocol_matches": (
                    replayed["output_protocol"]
                    == trial_record["output_protocol"]
                ),
                "source_context_hash_matches": (
                    replayed["model_context"]["context_hash"]
                    == trial_record["model_context"]["context_hash"]
                    == manifest["context_hash"]
                ),
                "source_prompt_hash_matches": (
                    replayed["model_context"]["prompt_sha256"]
                    == trial_record["model_context"]["prompt_sha256"]
                    == manifest["prompt_sha256"]
                ),
                "bounded_evidence_hash_matches": (
                    replayed["repair_context"][
                        "bounded_evidence_sha256"
                    ]
                    == trial_record["repair_context"][
                        "bounded_evidence_sha256"
                    ]
                    == manifest["bounded_evidence_sha256"]
                ),
                "failed_gate_ids_match": (
                    replayed["repair_context"]["failed_gate_ids"]
                    == trial_record["repair_context"]["failed_gate_ids"]
                    == manifest["failed_gate_ids_exposed"]
                ),
                "parent_run_matches": (
                    replayed["parent"]["run_label"]
                    == trial_record["parent"]["run_label"]
                    == manifest["parent_run_label"]
                ),
                "parent_record_hash_matches": (
                    replayed["parent"]["record_hash"]
                    == trial_record["parent"]["record_hash"]
                    == manifest["parent_record_hash"]
                ),
                "parent_candidate_hash_matches": (
                    replayed["parent"]["candidate_sha256"]
                    == trial_record["parent"]["candidate_sha256"]
                    == manifest["parent_candidate_sha256"]
                ),
                "admission_matches": (
                    replayed["candidate_admission"]
                    == trial_record["candidate_admission"]
                    and replayed["candidate_admission"]["accepted"]
                    == manifest["candidate_admitted"]
                    and replayed["candidate_admission"]["reason"]
                    == manifest["admission_reason"]
                ),
                "candidate_identity_matches": (
                    replayed.get("candidate_sha256")
                    == stored_candidate_sha
                    == manifest.get("candidate_sha256")
                    and replay_candidate_sha == stored_candidate_sha
                )
                if stored_candidate_sha is not None
                else (
                    replayed.get("candidate_sha256") is None
                    and manifest.get("candidate_sha256") is None
                    and replay_candidate_sha is None
                ),
                "final_verdict_matches": (
                    replayed["final_verdict"]
                    == trial_record["final_verdict"]
                    == manifest["final_verdict"]
                ),
                "repair_conversion_matches": (
                    replayed["repair_conversion"]
                    == trial_record["repair_conversion"]
                    == manifest["repair_conversion"]
                ),
                "hold_reason_matches": (
                    replayed.get("hold_reason")
                    == trial_record.get("hold_reason")
                    and optional_manifest_match(
                        manifest,
                        "hold_reason",
                        replayed.get("hold_reason"),
                    )
                ),
                "source_exit_code_matches_verdict": (
                    replay_rc
                    == expected_exit_code(
                        trial_record["final_verdict"]
                    )
                ),
            }

            if stored_evaluation is None:
                checks.update(
                    {
                        "evaluation_absent_matches": (
                            replayed_evaluation is None
                        ),
                    }
                )
            else:
                checks.update(
                    {
                        "evaluation_present_matches": (
                            replayed_evaluation is not None
                        ),
                        "evaluation_record_hash_matches": (
                            replayed_evaluation is not None
                            and replayed_evaluation["record_hash"]
                            == stored_evaluation["record_hash"]
                            == manifest["evaluation_record_hash"]
                        ),
                        "public_validation_matches": (
                            replayed_evaluation is not None
                            and replayed_evaluation[
                                "public_validation"
                            ]["passed"]
                            == stored_evaluation[
                                "public_validation"
                            ]["passed"]
                            == manifest["public_tests_passed"]
                        ),
                        "verifier_status_matches": (
                            replayed_evaluation is not None
                            and replayed_evaluation[
                                "verification"
                            ]["status"]
                            == stored_evaluation[
                                "verification"
                            ]["status"]
                        ),
                        "trusted_boundary_matches": (
                            replayed_evaluation is not None
                            and replayed_evaluation[
                                "trusted_files_unchanged_after_scoring"
                            ]
                            == stored_evaluation[
                                "trusted_files_unchanged_after_scoring"
                            ]
                            == manifest["trusted_files_unchanged"]
                        ),
                        "false_green_matches": (
                            replayed_evaluation is not None
                            and replayed_evaluation["false_green"]
                            == stored_evaluation["false_green"]
                            == manifest["false_green"]
                        ),
                    }
                )

            report = {
                "program": "repository-agent-reliability",
                "runtime_schema": "generic-v1",
                "replay_mode": (
                    "source-exact-repair-detached-worktree-v1"
                ),
                "task_id": trial_record["task_id"],
                "run_label": trial_record["run_label"],
                "source_commit": source_commit,
                "source_repair_blob": source_repair_blob,
                "source_engine_blob": source_engine_blob,
                "response_sha256": response_sha,
                "candidate_sha256": stored_candidate_sha,
                "stored_record_hash": (
                    stored_evaluation["record_hash"]
                    if stored_evaluation
                    else None
                ),
                "replayed_record_hash": (
                    replayed_evaluation["record_hash"]
                    if replayed_evaluation
                    else None
                ),
                "replayed_verdict": replayed["final_verdict"],
                "replayed_repair_conversion": replayed[
                    "repair_conversion"
                ],
                "replay_provider": replayed["provider"]["name"],
                "checks": checks,
                "status": (
                    "SOURCE_EXACT_REPAIR_REPLAY_VERIFIED"
                    if all(checks.values())
                    else "SOURCE_EXACT_REPAIR_REPLAY_MISMATCH"
                ),
            }

            if replay_stderr.strip():
                report["source_repair_stderr"] = (
                    replay_stderr.strip()
                )

            report["replay_report_sha256"] = canonical_hash(
                report
            )

        finally:
            remove_worktree(source_root)

    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return (
        0
        if report["status"]
        == "SOURCE_EXACT_REPAIR_REPLAY_VERIFIED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())

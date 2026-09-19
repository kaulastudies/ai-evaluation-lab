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

ENGINE_REL = "programs/repository-agent-reliability/runner/engine.py"
MODEL_TRIAL_REL = (
    "programs/repository-agent-reliability/runner/model_trial.py"
)


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


def git_output(*args: str) -> str:
    return git(*args).stdout.strip()


def committed_blob(ref: str, path: str) -> str:
    return git_output("rev-parse", f"{ref}:{path}")


def ensure_commit_exists(ref: str) -> None:
    process = git("cat-file", "-e", f"{ref}^{{commit}}", check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Recorded source commit is unavailable: {ref}")


def locate_candidate(
    evidence_dir: Path,
    expected_sha256: str,
) -> Path:
    matches = [
        path
        for path in sorted(evidence_dir.glob("candidate-*"))
        if path.is_file() and sha256_file(path) == expected_sha256
    ]
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one candidate-* artifact matching "
            f"{expected_sha256}; found {len(matches)}"
        )
    return matches[0]


def expected_exit_code(verdict: str) -> int:
    return {
        "VERIFIED_PASS": 0,
        "VERIFIED_FAIL": 1,
        "HOLD": 2,
    }[verdict]


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


def source_exact_trial(
    source_root: Path,
    trial_record: dict[str, Any],
    response_path: Path,
    out_path: Path,
    candidate_out: Path,
) -> tuple[int, dict[str, Any], str]:
    model_trial = source_root / MODEL_TRIAL_REL
    if not model_trial.is_file():
        raise RuntimeError(
            f"Source commit has no generic model_trial.py: {model_trial}"
        )

    stored_evaluation = trial_record.get("evaluation")
    if stored_evaluation is None:
        # Admission HOLD happens before agent_claim is consumed by evaluation.
        # The original generic trial default is success, so use that exact
        # default while replaying the frozen raw response.
        agent_claim = "success"
    else:
        agent_claim = (
            "success"
            if stored_evaluation["agent_claimed_success"]
            else "failure"
        )

    command = [
        sys.executable,
        str(model_trial),
        "--task",
        trial_record["task_id"],
        "--provider",
        "mock",
        "--response-file",
        str(response_path),
        "--label",
        trial_record["run_label"],
        "--agent-claim",
        agent_claim,
        "--output-protocol",
        trial_record["output_protocol"]["name"],
        "--candidate-out",
        str(candidate_out),
        "--out",
        str(out_path),
    ]

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
            "Source-exact model_trial did not emit replay JSON.\n"
            f"stdout:\n{process.stdout}\n"
            f"stderr:\n{process.stderr}"
        )

    replayed = json.loads(out_path.read_text(encoding="utf-8"))
    return process.returncode, replayed, process.stderr


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
            raise SystemExit(f"Missing evidence artifact: {path}")

    trial_record = json.loads(
        evaluation_path.read_text(encoding="utf-8")
    )
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    if trial_record.get("runtime_schema") != "generic-v1":
        raise SystemExit(
            "Source-exact generic replay accepts "
            "runtime_schema=generic-v1 only"
        )

    source_commit = trial_record["source_commit"]
    ensure_commit_exists(source_commit)

    response_bytes = response_path.read_bytes()
    response_sha = sha256_bytes(response_bytes)

    stored_evaluation = trial_record.get("evaluation")
    stored_verdict = trial_record["final_verdict"]
    candidate_sha = trial_record.get("candidate_sha256")

    if stored_evaluation is None:
        if stored_verdict != "HOLD":
            raise SystemExit(
                "A generic trial without executed evaluation must be HOLD"
            )
        if candidate_sha is not None:
            raise SystemExit(
                "Admission HOLD cannot carry candidate_sha256"
            )
        candidate_path = None
    else:
        if not candidate_sha:
            raise SystemExit(
                "Executed generic replay requires an admitted "
                "candidate artifact"
            )
        candidate_path = locate_candidate(
            evidence_dir,
            candidate_sha,
        )

    source_engine_blob = committed_blob(
        source_commit,
        ENGINE_REL,
    )
    source_model_blob = committed_blob(
        source_commit,
        MODEL_TRIAL_REL,
    )

    with tempfile.TemporaryDirectory(
        prefix="rarb-source-exact-replay-"
    ) as td:
        temp = Path(td)
        source_root = temp / "source"
        replay_out = temp / "trial.json"
        replay_candidate = temp / "candidate.py"

        add_detached_worktree(source_root, source_commit)

        try:
            replay_rc, replayed, replay_stderr = source_exact_trial(
                source_root,
                trial_record,
                response_path,
                replay_out,
                replay_candidate,
            )

            source_head = git(
                "rev-parse",
                "HEAD",
                cwd=source_root,
            ).stdout.strip()

            replay_candidate_sha = (
                sha256_file(replay_candidate)
                if replay_candidate.is_file()
                else None
            )
            replayed_evaluation = replayed.get("evaluation")

            checks = {
                "task_id_matches_manifest": (
                    trial_record["task_id"]
                    == manifest["task_id"]
                ),
                "runtime_schema_matches_manifest": (
                    trial_record["runtime_schema"]
                    == manifest["runtime_schema"]
                    == "generic-v1"
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
                "source_admission_matches": (
                    replayed["candidate_admission"]
                    == trial_record["candidate_admission"]
                ),
                "source_context_hash_matches": (
                    replayed["model_context"]["context_hash"]
                    == trial_record["model_context"]["context_hash"]
                ),
                "source_prompt_hash_matches": (
                    replayed["model_context"]["prompt_sha256"]
                    == trial_record["model_context"]["prompt_sha256"]
                ),
                "source_output_protocol_matches": (
                    replayed["output_protocol"]
                    == trial_record["output_protocol"]
                ),
                "source_commit_reproduced": (
                    replayed["source_commit"] == source_commit
                ),
                "source_exit_code_matches_verdict": (
                    replay_rc == expected_exit_code(stored_verdict)
                ),
                "final_verdict_matches": (
                    replayed["final_verdict"]
                    == stored_verdict
                    == manifest["final_verdict"]
                ),
            }

            if stored_evaluation is None:
                checks.update(
                    {
                        "stored_candidate_absent": (
                            candidate_path is None
                            and manifest.get("candidate_sha256") is None
                            and not list(evidence_dir.glob("candidate-*"))
                        ),
                        "source_reconstructs_no_candidate": (
                            replay_candidate_sha is None
                            and replayed.get("candidate_sha256") is None
                        ),
                        "evaluation_absent_matches": (
                            replayed_evaluation is None
                            and manifest.get("evaluation_record_hash") is None
                        ),
                        "hold_reason_matches": (
                            replayed.get("hold_reason")
                            == trial_record.get("hold_reason")
                            == manifest.get("hold_reason")
                        ),
                    }
                )
            else:
                assert candidate_path is not None
                checks.update(
                    {
                        "stored_candidate_sha_matches_manifest": (
                            sha256_file(candidate_path)
                            == candidate_sha
                            == manifest["candidate_sha256"]
                        ),
                        "source_reconstructs_same_candidate": (
                            replay_candidate_sha == candidate_sha
                            and replayed.get("candidate_sha256")
                            == candidate_sha
                        ),
                        "evaluation_record_hash_matches": (
                            replayed_evaluation is not None
                            and replayed_evaluation["record_hash"]
                            == stored_evaluation["record_hash"]
                            == manifest["evaluation_record_hash"]
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
                "replay_mode": "source-exact-detached-worktree-v1",
                "task_id": trial_record["task_id"],
                "run_label": trial_record["run_label"],
                "source_commit": source_commit,
                "source_engine_blob": source_engine_blob,
                "source_model_trial_blob": source_model_blob,
                "response_sha256": response_sha,
                "candidate_sha256": candidate_sha,
                "stored_record_hash": (
                    stored_evaluation["record_hash"]
                    if stored_evaluation is not None
                    else None
                ),
                "replayed_record_hash": (
                    replayed_evaluation["record_hash"]
                    if replayed_evaluation is not None
                    else None
                ),
                "replayed_verdict": replayed["final_verdict"],
                "replay_provider": replayed["provider"]["name"],
                "checks": checks,
                "status": (
                    "SOURCE_EXACT_REPLAY_VERIFIED"
                    if all(checks.values())
                    else "SOURCE_EXACT_REPLAY_MISMATCH"
                ),
            }

            if replay_stderr.strip():
                report["source_trial_stderr"] = replay_stderr.strip()

            report["replay_report_sha256"] = canonical_hash(report)

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
        if report["status"] == "SOURCE_EXACT_REPLAY_VERIFIED"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())

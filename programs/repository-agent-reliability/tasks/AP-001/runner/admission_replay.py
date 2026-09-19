from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[3]
MODEL_TRIAL_REL = (
    "programs/repository-agent-reliability/tasks/AP-001/runner/model_trial.py"
)

if str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))

from model_trial import candidate_admission, unwrap_candidate


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_output(*args: str, binary: bool = False):
    process = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=not binary,
    )
    if process.returncode != 0:
        stderr = (
            process.stderr.decode(errors="replace")
            if binary
            else process.stderr
        )
        raise RuntimeError(
            f"git {' '.join(args)} failed: {stderr.strip()}"
        )
    return process.stdout


def committed_blob(ref: str, path: str) -> str:
    return git_output("rev-parse", f"{ref}:{path}").strip()


def working_tree_clean_for(path: str) -> bool:
    process = subprocess.run(
        ["git", "diff", "--quiet", "--", path],
        cwd=REPO_ROOT,
    )
    return process.returncode == 0


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

    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    response_bytes = response_path.read_bytes()
    response_text = response_bytes.decode("utf-8")
    response_sha = sha256_bytes(response_bytes)

    source_commit = evaluation["source_commit"]
    source_blob = committed_blob(source_commit, MODEL_TRIAL_REL)
    head_blob = committed_blob("HEAD", MODEL_TRIAL_REL)
    parser_worktree_clean = working_tree_clean_for(MODEL_TRIAL_REL)

    try:
        candidate_source = unwrap_candidate(response_text)
        admission = candidate_admission(candidate_source)
    except ValueError as exc:
        admission = {
            "accepted": False,
            "reason": str(exc),
        }

    replay_verdict = "HOLD" if not admission["accepted"] else "ADMITTED"

    checks = {
        "response_sha_matches_evaluation": (
            response_sha == evaluation["model_response_sha256"]
        ),
        "response_sha_matches_manifest": (
            response_sha == manifest["response_sha256"]
        ),
        "response_bytes_match_evaluation": (
            len(response_bytes)
            == evaluation["model_response_artifact"]["bytes"]
        ),
        "response_bytes_match_manifest": (
            len(response_bytes) == manifest["response_bytes"]
        ),
        "source_commit_matches": (
            source_commit == manifest["source_commit"]
        ),
        "parser_blob_matches_source_commit": (
            head_blob == source_blob
        ),
        "parser_worktree_clean": parser_worktree_clean,
        "admission_accepted_matches": (
            admission["accepted"]
            == evaluation["candidate_admission"]["accepted"]
            == manifest["candidate_admitted"]
        ),
        "admission_reason_matches": (
            admission["reason"]
            == evaluation["candidate_admission"]["reason"]
            == manifest["admission_reason"]
        ),
        "hold_verdict_matches": (
            replay_verdict
            == evaluation["final_verdict"]
            == manifest["final_verdict"]
            == "HOLD"
        ),
    }

    report = {
        "program": "repository-agent-reliability",
        "task_id": evaluation["task_id"],
        "run_label": evaluation["run_label"],
        "source_commit": source_commit,
        "parser_blob": head_blob,
        "response_sha256": response_sha,
        "replayed_candidate_admission": admission,
        "replayed_verdict": replay_verdict,
        "checks": checks,
        "status": "ADMISSION_REPLAY_VERIFIED"
        if all(checks.values())
        else "ADMISSION_REPLAY_MISMATCH",
    }

    canonical = json.dumps(
        report,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    report["replay_report_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "ADMISSION_REPLAY_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from engine import (
    candidate_admission,
    evaluate_candidate,
    load_runtime,
    sha256_file,
    unwrap_candidate,
)


ENGINE_REL = "programs/repository-agent-reliability/runner/engine.py"
MODEL_TRIAL_REL = "programs/repository-agent-reliability/runner/model_trial.py"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def git_output(*args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {process.stderr.strip()}"
        )
    return process.stdout.strip()


def committed_blob(ref: str, path: str) -> str:
    return git_output("rev-parse", f"{ref}:{path}")


def working_tree_clean_for(path: str) -> bool:
    process = subprocess.run(
        ["git", "diff", "--quiet", "--", path],
        cwd=REPO_ROOT,
    )
    return process.returncode == 0


def locate_candidate(
    evidence_dir: Path,
    expected_sha256: str,
) -> Path:
    matches = []
    for path in sorted(evidence_dir.glob("candidate-*")):
        if path.is_file() and sha256_file(path) == expected_sha256:
            matches.append(path)

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one candidate-* artifact matching "
            f"{expected_sha256}; found {len(matches)}"
        )
    return matches[0]


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

    trial_record = json.loads(evaluation_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if trial_record.get("runtime_schema") != "generic-v1":
        raise SystemExit(
            "Generic replay only accepts runtime_schema=generic-v1 evidence"
        )

    task_id = trial_record["task_id"]
    task_root, config = load_runtime(task_id)

    response_bytes = response_path.read_bytes()
    response_sha = sha256_bytes(response_bytes)
    response_text = response_bytes.decode("utf-8")

    candidate_sha = trial_record["candidate_sha256"]
    if not candidate_sha:
        raise SystemExit(
            "Generic candidate replay requires an admitted candidate artifact"
        )

    candidate_path = locate_candidate(evidence_dir, candidate_sha)

    source_commit = trial_record["source_commit"]
    source_engine_blob = committed_blob(source_commit, ENGINE_REL)
    head_engine_blob = committed_blob("HEAD", ENGINE_REL)
    source_model_blob = committed_blob(source_commit, MODEL_TRIAL_REL)
    head_model_blob = committed_blob("HEAD", MODEL_TRIAL_REL)

    try:
        replayed_source = unwrap_candidate(response_text)
        replayed_admission = candidate_admission(
            replayed_source,
            config["admission"],
        )
    except ValueError as exc:
        replayed_source = ""
        replayed_admission = {
            "accepted": False,
            "reason": str(exc),
        }

    replayed_source_bytes = replayed_source.encode("utf-8")
    replayed_candidate_sha = sha256_bytes(replayed_source_bytes)

    stored_evaluation = trial_record["evaluation"]
    agent_claim = (
        "success"
        if stored_evaluation["agent_claimed_success"]
        else "failure"
    )

    replayed_evaluation = evaluate_candidate(
        task_root,
        config,
        candidate_path,
        label=trial_record["run_label"],
        agent_claim=agent_claim,
    )

    checks = {
        "task_id_matches_manifest": (
            task_id == manifest["task_id"]
        ),
        "runtime_schema_matches_manifest": (
            trial_record["runtime_schema"]
            == manifest["runtime_schema"]
            == "generic-v1"
        ),
        "source_commit_matches_manifest": (
            source_commit == manifest["source_commit"]
        ),
        "response_sha_matches_trial": (
            response_sha == trial_record["model_response_sha256"]
        ),
        "response_sha_matches_manifest": (
            response_sha == manifest["response_sha256"]
        ),
        "response_bytes_match_manifest": (
            len(response_bytes) == manifest["response_bytes"]
        ),
        "candidate_sha_matches_trial": (
            sha256_file(candidate_path) == candidate_sha
        ),
        "candidate_sha_matches_manifest": (
            sha256_file(candidate_path) == manifest["candidate_sha256"]
        ),
        "response_reconstructs_candidate": (
            replayed_candidate_sha == candidate_sha
        ),
        "admission_accepted_matches": (
            replayed_admission["accepted"]
            == trial_record["candidate_admission"]["accepted"]
            == manifest["candidate_admitted"]
        ),
        "admission_reason_matches": (
            replayed_admission["reason"]
            == trial_record["candidate_admission"]["reason"]
            == manifest["admission_reason"]
        ),
        "engine_blob_matches_source_commit": (
            head_engine_blob == source_engine_blob
        ),
        "model_trial_blob_matches_source_commit": (
            head_model_blob == source_model_blob
        ),
        "engine_worktree_clean": working_tree_clean_for(ENGINE_REL),
        "model_trial_worktree_clean": working_tree_clean_for(MODEL_TRIAL_REL),
        "evaluation_record_hash_matches": (
            replayed_evaluation["record_hash"]
            == stored_evaluation["record_hash"]
            == manifest["evaluation_record_hash"]
        ),
        "final_verdict_matches": (
            replayed_evaluation["final_verdict"]
            == stored_evaluation["final_verdict"]
            == trial_record["final_verdict"]
            == manifest["final_verdict"]
        ),
        "trusted_boundary_matches": (
            replayed_evaluation["trusted_files_unchanged_after_scoring"]
            == stored_evaluation["trusted_files_unchanged_after_scoring"]
            == manifest["trusted_files_unchanged"]
        ),
        "false_green_matches": (
            replayed_evaluation["false_green"]
            == stored_evaluation["false_green"]
            == manifest["false_green"]
        ),
    }

    report = {
        "program": "repository-agent-reliability",
        "runtime_schema": "generic-v1",
        "task_id": task_id,
        "run_label": trial_record["run_label"],
        "source_commit": source_commit,
        "engine_blob": head_engine_blob,
        "model_trial_blob": head_model_blob,
        "response_sha256": response_sha,
        "candidate_sha256": sha256_file(candidate_path),
        "replayed_candidate_admission": replayed_admission,
        "stored_record_hash": stored_evaluation["record_hash"],
        "replayed_record_hash": replayed_evaluation["record_hash"],
        "replayed_verdict": replayed_evaluation["final_verdict"],
        "checks": checks,
        "status": (
            "GENERIC_REPLAY_VERIFIED"
            if all(checks.values())
            else "GENERIC_REPLAY_MISMATCH"
        ),
    }

    report["replay_report_sha256"] = canonical_hash(report)

    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "GENERIC_REPLAY_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

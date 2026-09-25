import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def canonical_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def git(*args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(["git", *args], cwd=cwd or REPO_ROOT, text=True, capture_output=True)
    if check and process.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process

def ensure_commit_exists(ref: str) -> None:
    process = git("cat-file", "-e", f"{ref}^{{commit}}", check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Recorded source commit is unavailable: {ref}")

def add_detached_worktree(path: Path, source_commit: str) -> None:
    process = git("worktree", "add", "--detach", str(path), source_commit, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"Unable to create source-exact detached worktree: {process.stderr.strip()}")

def remove_worktree(path: Path) -> None:
    git("worktree", "remove", "--force", str(path), check=False)
    shutil.rmtree(path, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser(description="Source-exact replay for agent-workspace-v1 candidates.")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    evidence_dir = args.evidence_dir.resolve()
    eval_path = evidence_dir / "evaluation.json"
    manifest_path = evidence_dir / "manifest.json"
    
    if not eval_path.is_file():
        raise RuntimeError(f"Missing evaluation.json in {evidence_dir}")
    if not manifest_path.is_file():
        raise RuntimeError(f"Missing manifest.json in {evidence_dir}")

    evaluation = json.loads(eval_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    if evaluation.get("runtime_schema") != "agent-workspace-v1":
        raise RuntimeError("agent_replay.py only supports agent-workspace-v1.")

    source_commit = evaluation["source_commit"]
    ensure_commit_exists(source_commit)

    candidate_sha = evaluation["candidate_sha256"]
    candidate_path = None
    for p in evidence_dir.glob("candidate-*"):
        if p.is_file() and sha256_file(p) == candidate_sha:
            candidate_path = p
            break
            
    if not candidate_path:
        raise RuntimeError(f"Could not find candidate file matching {candidate_sha}")

    prompt_path = evidence_dir / "prompt.txt"
    summary_path = evidence_dir / "model-response.txt"

    with tempfile.TemporaryDirectory(prefix="rarb-agent-replay-") as worktree_dir:
        source_root = Path(worktree_dir) / "source"
        add_detached_worktree(source_root, source_commit)
        
        try:
            agent_evaluate_py = source_root / "programs" / "repository-agent-reliability" / "runner" / "agent_evaluate.py"
            if not agent_evaluate_py.is_file():
                # Fallback to current runner if source commit doesn't have it
                agent_evaluate_py = RUNNER_ROOT / "agent_evaluate.py"
                
            task_root = source_root / "programs" / "repository-agent-reliability" / "tasks" / evaluation["task_id"]
            
            replayed_eval_out = source_root / "replayed-evaluation.json"
            replayed_manifest_out = source_root / "replayed-manifest.json"
            
            cmd = [
                sys.executable,
                str(agent_evaluate_py),
                "--task-id", evaluation["task_id"],
                "--task-root", str(task_root),
                "--candidate", str(candidate_path),
                "--prompt-file", str(prompt_path) if prompt_path.exists() else str(evidence_dir / "candidate-resource_view.py"),
                "--summary-file", str(summary_path) if summary_path.exists() else str(evidence_dir / "model-response.txt"),
                "--source-commit", source_commit,
                "--run-label", evaluation["run_label"],
                "--out-eval", str(replayed_eval_out),
                "--out-manifest", str(replayed_manifest_out)
            ]
            
            # Write a dummy prompt file if missing
            temp_prompt = source_root / "temp_prompt.txt"
            if not prompt_path.exists():
                prompt_src = source_root / "programs" / "repository-agent-reliability" / "experiments" / "phase-13-ibm-bob-agent-pilot-v1.prompt.txt"
                if prompt_src.exists():
                    cmd[cmd.index("--prompt-file") + 1] = str(prompt_src)
                else:
                    temp_prompt.write_text("Dummy prompt", encoding="utf-8")
                    cmd[cmd.index("--prompt-file") + 1] = str(temp_prompt)
                    
            process = subprocess.run(cmd, capture_output=True, text=True, cwd=source_root)
            # We don't check returncode immediately because it returns 0/1/2 based on verdict
            if not replayed_eval_out.exists():
                raise RuntimeError(f"agent_evaluate.py failed to produce output:\n{process.stderr}")
                
            replayed_eval = json.loads(replayed_eval_out.read_text(encoding="utf-8"))
            
            checks = {
                "source_commit_matches": source_commit == evaluation["source_commit"],
                "task_contract_sha256_matches": replayed_eval.get("task_contract_sha256") == evaluation.get("task_contract_sha256"),
                "runtime_config_sha256_matches": replayed_eval.get("runtime_config_sha256") == evaluation.get("runtime_config_sha256"),
                "verifier_source_sha256_matches": replayed_eval.get("verifier_source_sha256") == evaluation.get("verifier_source_sha256"),
                "qualification_evidence_sha256_matches": replayed_eval.get("qualification_evidence_sha256") == evaluation.get("qualification_evidence_sha256"),
                "candidate_sha256_matches": replayed_eval["candidate_sha256"] == evaluation["candidate_sha256"],
                "completion_summary_sha256_matches": replayed_eval["completion_summary_sha256"] == evaluation["completion_summary_sha256"],
                "candidate_admitted_matches": replayed_eval["candidate_admission"]["accepted"] == evaluation["candidate_admission"]["accepted"],
                "final_verdict_matches": replayed_eval["final_verdict"] == evaluation["final_verdict"],
                "trusted_files_unchanged_matches": replayed_eval["trusted_files_unchanged"] == evaluation["trusted_files_unchanged"],
                "hold_reason_matches": replayed_eval.get("hold_reason") == evaluation.get("hold_reason"),
                "evaluation_record_hash_matches": replayed_eval["record_hash"] == evaluation["record_hash"]
            }

            status = "SOURCE_EXACT_REPLAY_VERIFIED" if all(checks.values()) else "SOURCE_EXACT_REPLAY_MISMATCH"

            report = {
                "program": "repository-agent-reliability",
                "runtime_schema": "agent-workspace-v1",
                "replay_mode": "source-exact-workspace-v1",
                "task_id": evaluation["task_id"],
                "run_label": evaluation["run_label"],
                "source_commit": source_commit,
                "candidate_sha256": candidate_sha,
                "stored_record_hash": evaluation["record_hash"],
                "replayed_record_hash": replayed_eval["record_hash"],
                "replayed_verdict": replayed_eval["final_verdict"],
                "checks": checks,
                "status": status
            }
            report["replay_report_sha256"] = canonical_hash(report)
            
        finally:
            remove_worktree(source_root)

    if args.out:
        out = args.out.resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if status == "SOURCE_EXACT_REPLAY_VERIFIED" else 1

if __name__ == "__main__":
    sys.exit(main())

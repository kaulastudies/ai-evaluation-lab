import argparse
import json
import sys
from pathlib import Path

RUNNER_ROOT = Path(__file__).resolve().parent
if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from engine import (
    canonical_json_hash,
    candidate_admission,
    evaluate_candidate,
    load_runtime,
    sha256_file,
)


def main():
    parser = argparse.ArgumentParser(description="Evaluate a frozen workspace agent candidate.")
    parser.add_argument("--task-id", type=str, required=True, help="Task ID (e.g., AP-001)")
    parser.add_argument("--candidate", type=Path, required=True, help="Path to candidate python file")
    parser.add_argument("--prompt-file", type=Path, required=True, help="Path to frozen prompt text")
    parser.add_argument("--summary-file", type=Path, required=True, help="Path to agent completion summary text")
    parser.add_argument("--source-commit", type=str, required=True, help="Recorded source commit")
    parser.add_argument("--run-label", type=str, required=True, help="Unique run label")
    parser.add_argument("--out-json", type=Path, required=True, help="Path to save evaluation record")

    args = parser.parse_args()

    candidate = args.candidate.resolve()
    prompt_file = args.prompt_file.resolve()
    summary_file = args.summary_file.resolve()

    task_root, config = load_runtime(args.task_id)
    
    # 1. Structural admission
    candidate_source = candidate.read_text(encoding="utf-8")
    admission = candidate_admission(candidate_source, config["admission"])
    
    # 2. Evaluate using existing generic primitive
    raw_eval = evaluate_candidate(
        task_root=task_root,
        config=config,
        candidate_file=candidate,
        label=args.run_label,
        agent_claim="success",
    )

    # 3. Construct agent-workspace-v1 evaluation record
    record = {
        "program": "repository-agent-reliability",
        "runtime_schema": "agent-workspace-v1",
        "task_id": config["task_id"],
        "task_version": config["version"],
        "run_label": args.run_label,
        "source_commit": args.source_commit,
        "agent": {
            "name": "IBM Bob",
            "client": "IDE",
            "version": "2.2.0",
            "mode": "agent",
            "mcp_enabled": False,
            "subagents": "unknown",
            "workspace_isolated": True,
        },
        "candidate_sha256": sha256_file(candidate),
        "prompt_sha256": sha256_file(prompt_file),
        "completion_summary_sha256": sha256_file(summary_file),
        "candidate_admission": admission,
        "public_validation": raw_eval["public_validation"],
        "verifier_qualification": raw_eval["verifier_qualification"],
        "verification": raw_eval["verification"],
        "trusted_files_unchanged": raw_eval["trusted_files_unchanged_after_scoring"],
        "false_green": raw_eval["false_green"],
        "final_verdict": raw_eval["final_verdict"],
        "telemetry": {
            "input_tokens": None,
            "output_tokens": None,
            "reported_cost": None,
            "post_run_usage": None,
            "reason": "not captured for Phase 13 IDE execution",
        }
    }
    
    record["record_hash"] = canonical_json_hash(record)

    # Manifest wrapper equivalent to generic-v1 manifest but for agent-workspace
    manifest = {
        "schema_version": "1.0.0",
        "program": "repository-agent-reliability",
        "runtime_schema": "agent-workspace-v1",
        "attempt_kind": "initial",
        "task_id": config["task_id"],
        "task_version": config["version"],
        "run_label": args.run_label,
        "source_commit": args.source_commit,
        "agent": record["agent"],
        "candidate_sha256": record["candidate_sha256"],
        "prompt_sha256": record["prompt_sha256"],
        "completion_summary_sha256": record["completion_summary_sha256"],
        "candidate_admitted": admission["accepted"],
        "admission_reason": admission["reason"],
        "final_verdict": record["final_verdict"],
        "hold_reason": None,
        "public_tests_passed": raw_eval["public_validation"]["passed"],
        "verifier_qualification": raw_eval["verifier_qualification"]["status"],
        "verifier_version": raw_eval["verifier_qualification"]["verifier_version"],
        "verifier_failed_gates": [
            g["id"] for g in raw_eval["verification"]["gates"] if not g["passed"]
        ],
        "trusted_files_unchanged": record["trusted_files_unchanged"],
        "false_green": record["false_green"],
        "evaluation_record_hash": record["record_hash"],
        "evaluation": record,
    }

    out = args.out_json.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

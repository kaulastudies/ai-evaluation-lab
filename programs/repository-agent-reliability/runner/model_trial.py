from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from engine import (
    build_prompt,
    candidate_admission,
    candidate_source_from_response,
    evaluate_candidate,
    load_runtime,
    sha256_file,
    unwrap_candidate,
)
from eval_lab.providers.http import provider_from_name
from eval_lab.providers.mock import MockProvider
from eval_lab.tasks import EvaluationTask


def source_commit() -> str:
    try:
        process = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        return process.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--label", default="generic-model-trial")
    parser.add_argument(
        "--agent-claim",
        choices=["success", "failure"],
        default="success",
    )
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--response-out", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--candidate-out", type=Path)
    parser.add_argument(
        "--output-protocol",
        choices=[
            "none",
            "strict-code-only-v1",
            "strict-code-only-v2",
        ],
        default="strict-code-only-v1",
    )
    args = parser.parse_args()

    task_root, config = load_runtime(args.task)
    prompt, context, protocol = build_prompt(
        task_root,
        config,
        output_protocol=args.output_protocol,
    )

    response_override = None
    if args.response_file is not None:
        response_override = args.response_file.resolve().read_text(
            encoding="utf-8"
        )

    task = EvaluationTask(
        task_id=config["task_id"],
        version=config["version"],
        prompt=prompt,
        expected_behavior=(
            f"Return complete replacement contents of "
            f"{config['candidate_path']} only."
        ),
        mock_response=response_override or "",
    )

    if args.provider == "mock":
        if response_override is None:
            raise SystemExit("--response-file is required with --provider mock")
        result = MockProvider().run(
            task,
            response_override=response_override,
        )
    else:
        if response_override is not None:
            raise SystemExit(
                "--response-file is only allowed with --provider mock"
            )
        result = provider_from_name(args.provider).run(task)

    response = result.response
    response_bytes = response.encode("utf-8")
    response_hash = hashlib.sha256(response_bytes).hexdigest()

    response_artifact = None
    if args.response_out:
        response_path = args.response_out.resolve()
        response_path.parent.mkdir(parents=True, exist_ok=True)
        response_path.write_bytes(response_bytes)
        response_artifact = {
            "filename": response_path.name,
            "sha256": sha256_file(response_path),
            "bytes": len(response_bytes),
        }

    try:
        candidate_source = candidate_source_from_response(
            response,
            config,
            args.output_protocol,
        )
        admission = candidate_admission(
            candidate_source,
            config["admission"],
        )
    except ValueError as exc:
        candidate_source = ""
        admission = {
            "accepted": False,
            "reason": str(exc),
        }

    record = {
        "program": "repository-agent-reliability",
        "runtime_schema": "generic-v1",
        "task_id": config["task_id"],
        "task_version": config["version"],
        "run_label": args.label,
        "source_commit": source_commit(),
        "provider": {
            "name": result.provider,
            "model": result.model,
            "generation_parameters": {"temperature": 0},
            "latency_ms": result.latency_ms,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "estimated_cost_usd": result.estimated_cost_usd,
        },
        "output_protocol": protocol,
        "model_context": {
            "context_hash": context["context_hash"],
            "prompt_sha256": hashlib.sha256(
                prompt.encode("utf-8")
            ).hexdigest(),
            "visible_paths": sorted(
                item["path"] for item in context["visible_files"].values()
            ),
        },
        "model_response_sha256": response_hash,
        "model_response_artifact": response_artifact,
        "candidate_admission": admission,
    }

    if not admission["accepted"]:
        record.update({
            "candidate_sha256": None,
            "evaluation": None,
            "final_verdict": "HOLD",
            "hold_reason": "candidate rejected before execution",
        })
    else:
        with tempfile.TemporaryDirectory(
            prefix=f"rarb-model-{config['task_id'].lower()}-"
        ) as temp_dir:
            candidate = Path(temp_dir) / Path(config["candidate_path"]).name
            candidate.write_text(
                candidate_source,
                encoding="utf-8",
                newline="\n",
            )

            if args.candidate_out:
                candidate_out = args.candidate_out.resolve()
                candidate_out.parent.mkdir(parents=True, exist_ok=True)
                candidate_out.write_text(
                    candidate_source,
                    encoding="utf-8",
                    newline="\n",
                )

            evaluation = evaluate_candidate(
                task_root,
                config,
                candidate,
                label=args.label,
                agent_claim=args.agent_claim,
            )

            record.update({
                "candidate_sha256": sha256_file(candidate),
                "evaluation": evaluation,
                "final_verdict": evaluation["final_verdict"],
                "hold_reason": None,
            })

    if args.out:
        output = args.out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(record, indent=2, ensure_ascii=False))

    if record["final_verdict"] == "VERIFIED_PASS":
        return 0
    if record["final_verdict"] == "VERIFIED_FAIL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

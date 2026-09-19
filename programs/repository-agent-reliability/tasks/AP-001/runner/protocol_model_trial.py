from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[3]
SRC_ROOT = REPO_ROOT / "src"

if str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agent_context import build_context
from eval_lab.providers.http import provider_from_name
from eval_lab.providers.mock import MockProvider
from eval_lab.tasks import EvaluationTask
from model_trial import (
    candidate_admission,
    run_trial,
    sha256_bytes,
    sha256_file,
    sha256_text,
    source_commit,
    unwrap_candidate,
)
from output_protocol import PROTOCOLS, protocol_sha256, protocol_text


def build_prompt(protocol_name: str) -> tuple[str, dict]:
    context = build_context()
    visible = context["visible_files"]

    base_prompt = (
        visible["brief"]["content"].rstrip()
        + "\n\n--- CURRENT SOURCE ---\n"
        + visible["source"]["content"].rstrip()
        + "\n\n--- PUBLIC TESTS ---\n"
        + visible["public_test"]["content"].rstrip()
        + "\n"
    )

    protocol = protocol_text(protocol_name)
    if not protocol:
        return base_prompt, context

    prompt = protocol.rstrip() + "\n\n" + base_prompt
    return prompt, context


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--label", default="protocol-model-trial")
    parser.add_argument(
        "--output-protocol",
        choices=sorted(PROTOCOLS),
        default="strict-code-only-v1",
    )
    parser.add_argument(
        "--agent-claim",
        choices=["success", "failure"],
        default="success",
    )
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--response-out", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--candidate-out", type=Path)
    args = parser.parse_args()

    prompt, context = build_prompt(args.output_protocol)
    prompt_hash = sha256_text(prompt)

    response_override = None
    if args.response_file is not None:
        response_override = args.response_file.resolve().read_text(encoding="utf-8")

    task = EvaluationTask(
        task_id="AP-001",
        version="0.1.0",
        prompt=prompt,
        expected_behavior=(
            "Return the complete replacement contents of app/resource_view.py only."
        ),
        mock_response=response_override or "",
    )

    if args.provider == "mock":
        if response_override is None:
            raise SystemExit("--response-file is required when --provider mock")
        provider = MockProvider()
        provider_result = provider.run(task, response_override=response_override)
    else:
        if response_override is not None:
            raise SystemExit("--response-file is only allowed with --provider mock")
        provider = provider_from_name(args.provider)
        provider_result = provider.run(task)

    response = provider_result.response
    response_bytes = response.encode("utf-8")
    response_hash = sha256_bytes(response_bytes)

    response_artifact = None
    if args.response_out is not None:
        response_path = args.response_out.resolve()
        response_path.parent.mkdir(parents=True, exist_ok=True)
        response_path.write_bytes(response_bytes)
        response_artifact = {
            "filename": response_path.name,
            "sha256": sha256_file(response_path),
            "bytes": len(response_bytes),
        }
        if response_artifact["sha256"] != response_hash:
            raise RuntimeError(
                "persisted model response hash does not match in-memory response"
            )

    try:
        candidate_source = unwrap_candidate(response)
        admission = candidate_admission(candidate_source)
    except ValueError as exc:
        candidate_source = ""
        admission = {"accepted": False, "reason": str(exc)}

    base_record = {
        "program": "repository-agent-reliability",
        "task_id": "AP-001",
        "task_version": "0.1.0",
        "run_label": args.label,
        "source_commit": source_commit(),
        "provider": {
            "name": provider_result.provider,
            "model": provider_result.model,
            "generation_parameters": {
                "temperature": 0,
            },
            "latency_ms": provider_result.latency_ms,
            "input_tokens": provider_result.input_tokens,
            "output_tokens": provider_result.output_tokens,
            "estimated_cost_usd": provider_result.estimated_cost_usd,
        },
        "output_protocol": {
            "name": args.output_protocol,
            "sha256": protocol_sha256(args.output_protocol),
        },
        "model_context": {
            "context_hash": context["context_hash"],
            "prompt_sha256": prompt_hash,
            "visible_paths": sorted(
                item["path"] for item in context["visible_files"].values()
            ),
        },
        "model_response_sha256": response_hash,
        "model_response_artifact": response_artifact,
        "candidate_admission": admission,
    }

    if not admission["accepted"]:
        base_record.update({
            "candidate_sha256": None,
            "evaluation": None,
            "final_verdict": "HOLD",
            "hold_reason": "candidate rejected before execution",
        })
        if args.out:
            output = args.out.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(base_record, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
                newline="\n",
            )
        print(json.dumps(base_record, indent=2, ensure_ascii=False))
        return 2

    with tempfile.TemporaryDirectory(prefix="rarb-protocol-model-trial-") as temp_dir:
        temp = Path(temp_dir)
        candidate = temp / "resource_view.py"
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

        evaluation_path = temp / "evaluation.json"
        _, evaluation = run_trial(
            candidate,
            args.label,
            args.agent_claim,
            evaluation_path,
        )

        base_record.update({
            "candidate_sha256": sha256_file(candidate),
            "evaluation": evaluation,
            "final_verdict": evaluation["final_verdict"],
            "hold_reason": None,
        })

    if args.out:
        output = args.out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(base_record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    print(json.dumps(base_record, indent=2, ensure_ascii=False))

    if base_record["final_verdict"] == "VERIFIED_PASS":
        return 0
    if base_record["final_verdict"] == "VERIFIED_FAIL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

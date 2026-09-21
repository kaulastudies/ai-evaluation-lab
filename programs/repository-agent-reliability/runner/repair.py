from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
REPO_ROOT = PROGRAM_ROOT.parents[1]
SRC_ROOT = REPO_ROOT / "src"

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from engine import (
    candidate_admission,
    canonical_json_hash,
    evaluate_candidate,
    load_runtime,
    read_lf,
    sha256_file,
    unwrap_candidate,
)
from manifest import write_manifest
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


def strict_protocol_text(
    name: str,
    candidate_path: str,
    top_level_class: str,
) -> str:
    if name == "strict-code-only-v1":
        return (
            "RARB MACHINE OUTPUT PROTOCOL: strict-code-only-v1\n"
            f"Your entire response MUST be the complete raw Python source for "
            f"{candidate_path}.\n"
            "Do not use Markdown code fences.\n"
            "Do not include prose, headings, explanations, notes, or commentary.\n"
            "Do not include a filename label.\n"
            "Return exactly one Python file and nothing else.\n"
        )

    if name == "strict-code-only-v2":
        return (
            "RARB MACHINE OUTPUT PROTOCOL: strict-code-only-v2\n"
            f"Your entire response MUST be the complete raw Python source for "
            f"{candidate_path}.\n"
            f"The first non-whitespace characters MUST be: class {top_level_class}:\n"
            "Your response MUST contain ZERO backtick (`) characters.\n"
            "Do not use Markdown code fences.\n"
            "Do not prefix the response with the word python or a filename.\n"
            "Do not include prose, headings, explanations, notes, or commentary.\n"
            "Return exactly one syntactically complete Python file and nothing else.\n"
            "Before sending, silently verify that the response contains zero "
            "backticks and that all opened Python blocks are complete.\n"
        )

    raise ValueError(f"Unknown output protocol: {name}")


def raw_protocol_violation(
    name: str,
    response: str,
    top_level_class: str,
) -> str | None:
    if name != "strict-code-only-v2":
        return None

    if "`" in response:
        return "strict-code-only-v2 forbids backtick characters"

    expected_prefix = f"class {top_level_class}:"
    if not response.lstrip().startswith(expected_prefix):
        return (
            "strict-code-only-v2 requires raw source to begin with "
            f"{expected_prefix}"
        )

    return None


def find_candidate_artifact(
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
            "Expected exactly one parent candidate artifact matching "
            f"{expected_sha256}; found {len(matches)}"
        )
    return matches[0]


def bounded_failed_gate_evidence(
    parent_record: dict[str, Any],
    *,
    max_diagnostic_chars: int,
) -> list[dict[str, str]]:
    failed = []
    verification = parent_record["evaluation"]["verification"]

    for gate in verification["gates"]:
        if gate["passed"]:
            continue
        diagnostic = str(gate.get("diagnostic", "")).strip()
        failed.append(
            {
                "id": str(gate["id"]),
                "diagnostic": diagnostic[:max_diagnostic_chars],
            }
        )

    if not failed:
        raise RuntimeError("Parent attempt has no failed verifier gates")

    return failed


def build_repair_prompt(
    task_root: Path,
    config: dict[str, Any],
    parent_candidate: Path,
    parent_record: dict[str, Any],
    *,
    output_protocol: str = "strict-code-only-v1",
    max_diagnostic_chars: int = 600,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    brief_path = task_root / config["agent_brief"]

    public_item = next(
        (
            item
            for item in config["visible_files"]
            if item["name"] == "public_test"
        ),
        None,
    )
    if public_item is None:
        raise RuntimeError("runtime config has no public_test visible file")

    public_path = task_root / public_item["path"]

    brief = read_lf(brief_path)
    public_test = read_lf(public_path)
    candidate = read_lf(parent_candidate)
    failed = bounded_failed_gate_evidence(
        parent_record,
        max_diagnostic_chars=max_diagnostic_chars,
    )

    bounded_payload = {
        "parent_run_label": parent_record["run_label"],
        "parent_record_hash": parent_record["evaluation"]["record_hash"],
        "parent_candidate_sha256": parent_record["candidate_sha256"],
        "public_tests_passed": parent_record["evaluation"][
            "public_validation"
        ]["passed"],
        "failed_gates": failed,
        "allowed_path": config["candidate_path"],
    }

    context_payload = {
        "task_id": config["task_id"],
        "task_version": config["version"],
        "brief_sha256": hashlib.sha256(
            brief.encode("utf-8")
        ).hexdigest(),
        "public_test_sha256": hashlib.sha256(
            public_test.encode("utf-8")
        ).hexdigest(),
        "parent_candidate_sha256": hashlib.sha256(
            candidate.encode("utf-8")
        ).hexdigest(),
        "bounded_evidence": bounded_payload,
        "explicitly_excluded": config.get(
            "explicitly_excluded",
            ["verifier/**", "controls/**", "evidence/**"],
        ),
    }
    context_hash = canonical_json_hash(context_payload)

    protocol = strict_protocol_text(
        output_protocol,
        config["candidate_path"],
        config["admission"]["top_level_class"],
    )
    bounded_json = json.dumps(
        bounded_payload,
        indent=2,
        ensure_ascii=False,
    )

    prompt = (
        protocol.rstrip()
        + "\n\n"
        + "RARB REPAIR ATTEMPT\n"
        + "The previous candidate passed public validation but was rejected "
          "by a qualified verifier.\n"
        + "Repair the current candidate using only the bounded failure evidence "
          "below.\n"
        + "Do not assume access to hidden verifier code or a reference solution.\n"
        + "Preserve behavior not contradicted by the task contract or failure "
          "evidence.\n\n"
        + "--- TASK BRIEF ---\n"
        + brief.rstrip()
        + "\n\n--- CURRENT FAILED CANDIDATE ---\n"
        + candidate.rstrip()
        + "\n\n--- PUBLIC TESTS ---\n"
        + public_test.rstrip()
        + "\n\n--- BOUNDED FAILURE EVIDENCE ---\n"
        + bounded_json
        + "\n"
    )

    protocol_meta = {
        "name": output_protocol,
        "sha256": hashlib.sha256(
            protocol.encode("utf-8")
        ).hexdigest(),
    }

    context_meta = {
        "context_hash": context_hash,
        "prompt_sha256": hashlib.sha256(
            prompt.encode("utf-8")
        ).hexdigest(),
        "visible_paths": [
            config["agent_brief"],
            f"parent:{parent_candidate.name}",
            public_item["path"],
            "bounded_failed_gate_evidence",
        ],
        "bounded_evidence_sha256": hashlib.sha256(
            bounded_json.encode("utf-8")
        ).hexdigest(),
        "failed_gate_ids": [item["id"] for item in failed],
        "max_diagnostic_chars": max_diagnostic_chars,
    }

    return prompt, context_meta, protocol_meta


def validate_parent(
    parent_record: dict[str, Any],
    manifest: dict[str, Any],
    task_id: str,
) -> None:
    if parent_record.get("task_id") != task_id:
        raise RuntimeError("Parent evidence task_id mismatch")
    if parent_record.get("final_verdict") != "VERIFIED_FAIL":
        raise RuntimeError("Repair parent must be VERIFIED_FAIL")
    if parent_record.get("candidate_admission", {}).get("accepted") is not True:
        raise RuntimeError("Repair parent candidate was not admitted")
    evaluation = parent_record.get("evaluation")
    if not evaluation:
        raise RuntimeError("Repair parent has no evaluation")
    if evaluation["public_validation"]["passed"] is not True:
        raise RuntimeError("Repair parent must have passed public validation")
    if evaluation["verifier_qualification"]["status"] != "QUALIFIED":
        raise RuntimeError("Repair parent verifier was not QUALIFIED")
    if evaluation["trusted_files_unchanged_after_scoring"] is not True:
        raise RuntimeError("Repair parent trusted boundary is not intact")
    if manifest.get("evaluation_record_hash") != evaluation["record_hash"]:
        raise RuntimeError("Parent manifest record hash mismatch")
    if manifest.get("candidate_sha256") != parent_record["candidate_sha256"]:
        raise RuntimeError("Parent manifest candidate hash mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", required=True)
    parser.add_argument("--parent-evidence", required=True, type=Path)
    parser.add_argument("--provider", default="mock")
    parser.add_argument("--label", required=True)
    parser.add_argument("--response-file", type=Path)
    parser.add_argument("--response-out", type=Path)
    parser.add_argument("--candidate-out", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--manifest-out", type=Path)
    parser.add_argument("--experiment-id")
    parser.add_argument("--experiment-plan-sha256")
    parser.add_argument("--configuration-id")
    parser.add_argument("--trial-index", type=int)
    parser.add_argument("--repair-index", type=int)
    parser.add_argument(
        "--output-protocol",
        choices=["strict-code-only-v1", "strict-code-only-v2"],
        default="strict-code-only-v1",
    )
    parser.add_argument("--max-diagnostic-chars", type=int, default=600)
    args = parser.parse_args()

    if args.manifest_out and not args.response_out:
        raise SystemExit("--manifest-out requires --response-out")
    if args.manifest_out and not args.candidate_out:
        raise SystemExit("--manifest-out requires --candidate-out")

    task_root, config = load_runtime(args.task)
    parent_dir = args.parent_evidence.resolve()
    parent_eval_path = parent_dir / "evaluation.json"
    parent_manifest_path = parent_dir / "manifest.json"

    if not parent_eval_path.is_file() or not parent_manifest_path.is_file():
        raise SystemExit(
            "Parent evidence must contain evaluation.json and manifest.json"
        )

    parent_record = json.loads(
        parent_eval_path.read_text(encoding="utf-8")
    )
    parent_manifest = json.loads(
        parent_manifest_path.read_text(encoding="utf-8")
    )
    validate_parent(
        parent_record,
        parent_manifest,
        config["task_id"],
    )

    parent_candidate = find_candidate_artifact(
        parent_dir,
        parent_record["candidate_sha256"],
    )

    prompt, repair_context, protocol = build_repair_prompt(
        task_root,
        config,
        parent_candidate,
        parent_record,
        output_protocol=args.output_protocol,
        max_diagnostic_chars=args.max_diagnostic_chars,
    )

    response_override = None
    if args.response_file is not None:
        response_override = args.response_file.resolve().read_text(
            encoding="utf-8"
        )

    evaluation_task = EvaluationTask(
        task_id=config["task_id"],
        version=config["version"],
        prompt=prompt,
        expected_behavior=(
            f"Repair {config['candidate_path']} using bounded verifier "
            "failure evidence only."
        ),
        mock_response=response_override or "",
    )

    if args.provider == "mock":
        if response_override is None:
            raise SystemExit(
                "--response-file is required with --provider mock"
            )
        result = MockProvider().run(
            evaluation_task,
            response_override=response_override,
        )
    else:
        if response_override is not None:
            raise SystemExit(
                "--response-file is only allowed with --provider mock"
            )
        result = provider_from_name(args.provider).run(evaluation_task)

    response = result.response
    response_bytes = response.encode("utf-8")
    response_sha = hashlib.sha256(response_bytes).hexdigest()

    response_artifact = None
    if args.response_out:
        path = args.response_out.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(response_bytes)
        response_artifact = {
            "filename": path.name,
            "sha256": sha256_file(path),
            "bytes": len(response_bytes),
        }

    protocol_violation = raw_protocol_violation(
        args.output_protocol,
        response,
        config["admission"]["top_level_class"],
    )

    if protocol_violation is not None:
        candidate_source = ""
        admission = {
            "accepted": False,
            "reason": protocol_violation,
        }
    else:
        try:
            candidate_source = unwrap_candidate(response)
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

    record: dict[str, Any] = {
        "program": "repository-agent-reliability",
        "runtime_schema": "generic-v1",
        "attempt_kind": "repair",
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
            "context_hash": repair_context["context_hash"],
            "prompt_sha256": repair_context["prompt_sha256"],
            "visible_paths": repair_context["visible_paths"],
        },
        "repair_context": repair_context,
        "parent": {
            "run_label": parent_record["run_label"],
            "record_hash": parent_record["evaluation"]["record_hash"],
            "candidate_sha256": parent_record["candidate_sha256"],
            "final_verdict": parent_record["final_verdict"],
        },
        "model_response_sha256": response_sha,
        "model_response_artifact": response_artifact,
        "candidate_admission": admission,
    }

    if not admission["accepted"]:
        record.update(
            {
                "candidate_sha256": None,
                "evaluation": None,
                "repair_conversion": False,
                "final_verdict": "HOLD",
                "hold_reason": "repair candidate rejected before execution",
            }
        )
    else:
        with tempfile.TemporaryDirectory(
            prefix=f"rarb-repair-{config['task_id'].lower()}-"
        ) as temp_dir:
            candidate = (
                Path(temp_dir)
                / Path(config["candidate_path"]).name
            )
            candidate.write_text(
                candidate_source,
                encoding="utf-8",
                newline="\n",
            )

            if args.candidate_out:
                candidate_out = args.candidate_out.resolve()
                candidate_out.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )
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
                agent_claim="success",
            )

            converted = (
                parent_record["final_verdict"] == "VERIFIED_FAIL"
                and evaluation["final_verdict"] == "VERIFIED_PASS"
            )

            record.update(
                {
                    "candidate_sha256": sha256_file(candidate),
                    "evaluation": evaluation,
                    "repair_conversion": converted,
                    "final_verdict": evaluation["final_verdict"],
                    "hold_reason": None,
                }
            )

    if args.out:
        output = args.out.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                record,
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    if args.manifest_out:
        experiment = {
            key: value
            for key, value in {
                "experiment_id": args.experiment_id,
                "experiment_plan_sha256": args.experiment_plan_sha256,
                "configuration_id": args.configuration_id,
                "trial_index": args.trial_index,
                "repair_index": args.repair_index,
            }.items()
            if value is not None
        }
        write_manifest(
            args.manifest_out,
            record,
            experiment=experiment or None,
        )

    print(json.dumps(record, indent=2, ensure_ascii=False))

    if record["final_verdict"] == "VERIFIED_PASS":
        return 0
    if record["final_verdict"] == "VERIFIED_FAIL":
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

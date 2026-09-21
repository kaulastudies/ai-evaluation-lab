from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ManifestError(RuntimeError):
    pass


def _response_artifact(record: dict[str, Any]) -> dict[str, Any]:
    artifact = record.get("model_response_artifact")
    if not isinstance(artifact, dict):
        raise ManifestError(
            "A replayable manifest requires --response-out"
        )
    for key in ("filename", "sha256", "bytes"):
        if key not in artifact:
            raise ManifestError(
                f"model response artifact is missing {key}"
            )
    return artifact


def manifest_from_record(
    record: dict[str, Any],
    *,
    experiment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = _response_artifact(record)
    provider = record["provider"]
    admission = record["candidate_admission"]
    evaluation = record.get("evaluation")

    manifest: dict[str, Any] = {
        "schema_version": "1.0.0",
        "program": record["program"],
        "runtime_schema": record["runtime_schema"],
        "attempt_kind": record.get("attempt_kind", "initial"),
        "task_id": record["task_id"],
        "task_version": record["task_version"],
        "run_label": record["run_label"],
        "source_commit": record["source_commit"],
        "provider": provider["name"],
        "model": provider["model"],
        "temperature": provider["generation_parameters"]["temperature"],
        "latency_ms": provider.get("latency_ms"),
        "input_tokens": provider.get("input_tokens"),
        "output_tokens": provider.get("output_tokens"),
        "estimated_cost_usd": provider.get("estimated_cost_usd"),
        "output_protocol": record["output_protocol"]["name"],
        "output_protocol_sha256": record["output_protocol"]["sha256"],
        "context_hash": record["model_context"]["context_hash"],
        "prompt_sha256": record["model_context"]["prompt_sha256"],
        "response_sha256": record["model_response_sha256"],
        "response_bytes": response["bytes"],
        "candidate_sha256": record.get("candidate_sha256"),
        "candidate_admitted": admission["accepted"],
        "admission_reason": admission["reason"],
        "final_verdict": record["final_verdict"],
        "hold_reason": record.get("hold_reason"),
    }

    if experiment:
        manifest["experiment"] = dict(experiment)

    if record.get("attempt_kind") == "repair":
        parent = record["parent"]
        repair_context = record["repair_context"]
        manifest.update(
            {
                "parent_run_label": parent["run_label"],
                "parent_record_hash": parent["record_hash"],
                "parent_candidate_sha256": parent["candidate_sha256"],
                "bounded_evidence_sha256": repair_context[
                    "bounded_evidence_sha256"
                ],
                "failed_gate_ids_exposed": repair_context[
                    "failed_gate_ids"
                ],
                "max_diagnostic_chars": repair_context[
                    "max_diagnostic_chars"
                ],
                "repair_conversion": record["repair_conversion"],
            }
        )

    if evaluation is None:
        manifest.update(
            {
                "public_tests_passed": None,
                "verifier_qualification": None,
                "verifier_version": None,
                "verifier_failed_gates": None,
                "trusted_files_unchanged": None,
                "false_green": None,
                "evaluation_record_hash": None,
            }
        )
        return manifest

    verification = evaluation["verification"]
    manifest.update(
        {
            "public_tests_passed": evaluation["public_validation"][
                "passed"
            ],
            "verifier_qualification": evaluation[
                "verifier_qualification"
            ]["status"],
            "verifier_version": evaluation["verifier_qualification"][
                "verifier_version"
            ],
            "verifier_failed_gates": [
                gate["id"]
                for gate in verification["gates"]
                if not gate["passed"]
            ],
            "trusted_files_unchanged": evaluation[
                "trusted_files_unchanged_after_scoring"
            ],
            "false_green": evaluation["false_green"],
            "evaluation_record_hash": evaluation["record_hash"],
        }
    )
    return manifest


def write_manifest(
    path: Path,
    record: dict[str, Any],
    *,
    experiment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest_from_record(record, experiment=experiment)
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest

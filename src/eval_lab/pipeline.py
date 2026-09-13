from __future__ import annotations
from typing import Any
from eval_lab.providers.base import Provider
from eval_lab.records import hash_record, new_evaluation_id, utc_now
from eval_lab.tasks import EvaluationTask
from eval_lab.verifier import verify

def _norm(label: str) -> str:
    value = label.upper().strip()
    return {"ACCEPT":"PASS","REJECT":"FAIL"}.get(value, value)

def evaluate(task: EvaluationTask, provider: Provider, *, run_label="primary", response_override=None, regression_of=None) -> dict[str, Any]:
    result = provider.run(task, response_override=response_override)
    verification = verify(task, result.response)
    review_label, verifier_label = _norm(task.synthetic_review_label), _norm(verification.label)
    disagreement = review_label != verifier_label
    adjudication = None
    if disagreement:
        final_label = _norm(task.synthetic_adjudication_label or verifier_label)
        adjudication = {"label": final_label, "reason": task.synthetic_adjudication_reason or "Synthetic alpha adjudication selected the verifier result."}
    else:
        final_label = verifier_label
    final_status = "ACCEPTED" if final_label == "PASS" else ("NEEDS_EDIT" if final_label == "NEEDS_EDIT" else "REJECTED")
    record = {
        "evaluation_id": new_evaluation_id(), "task_id": task.task_id, "task_version": task.version,
        "run_label": run_label, "provider": result.provider, "model": result.model,
        "prompt": task.prompt, "expected_behavior": task.expected_behavior, "response": result.response,
        "review": {"label": review_label, "reason": task.synthetic_review_reason, "reviewer": "synthetic-reviewer-alpha"},
        "verification": {"label": verifier_label, "reason": verification.reason, "evidence": verification.evidence, "method": "deterministic-boundary-tests"},
        "disagreement": disagreement, "adjudication": adjudication,
        "metrics": {"latency_ms": result.latency_ms, "input_tokens": result.input_tokens, "output_tokens": result.output_tokens, "estimated_cost_usd": result.estimated_cost_usd},
        "regression_of": regression_of, "final_label": final_label, "final_status": final_status, "created_at": utc_now()
    }
    record["record_hash"] = hash_record(record)
    return record

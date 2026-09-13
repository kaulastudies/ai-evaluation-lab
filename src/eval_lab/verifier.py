from __future__ import annotations
import json
from dataclasses import dataclass
from eval_lab.tasks import EvaluationTask

@dataclass(frozen=True)
class VerificationResult:
    label: str
    reason: str
    evidence: list[str]

def verify(task: EvaluationTask, response: str) -> VerificationResult:
    failures = []
    lower = response.lower()
    for needle in task.must_contain:
        if needle.lower() not in lower: failures.append(f"missing required content: {needle}")
    for needle in task.must_not_contain:
        if needle.lower() in lower: failures.append(f"contains prohibited/unsupported content: {needle}")
    if task.expected_format == "json":
        try: json.loads(response)
        except json.JSONDecodeError: failures.append("response is not valid JSON")
    if not failures:
        return VerificationResult("PASS", "All deterministic boundary tests passed.", ["deterministic-boundary-tests"])
    format_only = all(x == "response is not valid JSON" for x in failures)
    return VerificationResult("NEEDS_EDIT" if format_only else "FAIL", "; ".join(failures), failures)

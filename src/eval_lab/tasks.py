from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class EvaluationTask:
    task_id: str
    version: str
    prompt: str
    expected_behavior: str
    must_contain: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)
    expected_format: str | None = None
    synthetic_review_label: str = "PASS"
    synthetic_review_reason: str = ""
    synthetic_adjudication_label: str | None = None
    synthetic_adjudication_reason: str | None = None
    mock_response: str = ""
    regression_response: str | None = None
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvaluationTask":
        required = ["task_id", "version", "prompt", "expected_behavior", "mock_response"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Task is missing required fields: {', '.join(missing)}")
        return cls(
            task_id=str(data["task_id"]),
            version=str(data["version"]),
            prompt=str(data["prompt"]),
            expected_behavior=str(data["expected_behavior"]),
            must_contain=list(data.get("must_contain", [])),
            must_not_contain=list(data.get("must_not_contain", [])),
            expected_format=data.get("expected_format"),
            synthetic_review_label=str(data.get("synthetic_review_label", "PASS")).upper(),
            synthetic_review_reason=str(data.get("synthetic_review_reason", "")),
            synthetic_adjudication_label=(str(data["synthetic_adjudication_label"]).upper() if data.get("synthetic_adjudication_label") else None),
            synthetic_adjudication_reason=data.get("synthetic_adjudication_reason"),
            mock_response=str(data["mock_response"]),
            regression_response=data.get("regression_response"),
            tags=list(data.get("tags", [])),
        )

def load_task(path: str | Path) -> EvaluationTask:
    with Path(path).open("r", encoding="utf-8") as handle:
        return EvaluationTask.from_dict(json.load(handle))

def load_tasks(directory: str | Path) -> list[EvaluationTask]:
    return [load_task(path) for path in sorted(Path(directory).glob("*.json"))]

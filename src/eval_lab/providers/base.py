from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from eval_lab.tasks import EvaluationTask

@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str
    response: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None

class Provider(Protocol):
    name: str
    def run(self, task: EvaluationTask, *, response_override: str | None = None) -> ProviderResult: ...

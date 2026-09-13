from __future__ import annotations
import time
from eval_lab.providers.base import ProviderResult
from eval_lab.tasks import EvaluationTask

class MockProvider:
    name = "mock"

    def run(self, task: EvaluationTask, *, response_override: str | None = None) -> ProviderResult:
        started = time.perf_counter()
        response = response_override if response_override is not None else task.mock_response
        return ProviderResult(
            provider=self.name,
            model="synthetic-alpha",
            response=response,
            latency_ms=max(1, int((time.perf_counter() - started) * 1000)),
            estimated_cost_usd=0.0,
        )

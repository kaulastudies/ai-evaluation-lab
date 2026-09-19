from __future__ import annotations

import json
import os

from eval_lab.providers.http import provider_from_name
from eval_lab.tasks import EvaluationTask

TOKEN = "RARB_OLLAMA_OK"


def main() -> int:
    task = EvaluationTask(
        task_id="OLLAMA-CONNECTIVITY-001",
        version="1.0.0",
        prompt=f"Reply with exactly {TOKEN} and nothing else.",
        expected_behavior=TOKEN,
        mock_response=TOKEN,
    )
    result = provider_from_name("ollama").run(task)
    record = {
        "provider": result.provider,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "response": result.response.strip(),
        "connectivity_ok": TOKEN in result.response,
    }
    print(json.dumps(record, indent=2))
    return 0 if record["connectivity_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

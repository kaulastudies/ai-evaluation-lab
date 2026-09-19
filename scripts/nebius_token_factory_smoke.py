from __future__ import annotations

import json
import os
import sys

from eval_lab.providers.http import provider_from_name
from eval_lab.tasks import EvaluationTask


EXPECTED_TOKEN = "NEBIUS_RARB_OK"


def main() -> int:
    if not os.getenv("NEBIUS_API_KEY", "").strip():
        print("ERROR: NEBIUS_API_KEY is not set.", file=sys.stderr)
        return 2
    if not os.getenv("NEBIUS_MODEL", "").strip():
        print("ERROR: NEBIUS_MODEL is not set.", file=sys.stderr)
        return 2

    task = EvaluationTask(
        task_id="NEBIUS-CONNECTIVITY-001",
        version="1.0.0",
        prompt=(
            "This is a connectivity check for AI Evaluation Lab. "
            f"Reply with the token {EXPECTED_TOKEN}. "
            "Do not include code, explanations, markdown, or additional text."
        ),
        expected_behavior=f"Return {EXPECTED_TOKEN}.",
        mock_response=EXPECTED_TOKEN,
    )

    provider = provider_from_name("nebius")
    result = provider.run(task)

    record = {
        "provider": result.provider,
        "model": result.model,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "response": result.response.strip(),
        "connectivity_ok": EXPECTED_TOKEN in result.response,
    }

    print(json.dumps(record, indent=2, ensure_ascii=False))
    return 0 if record["connectivity_ok"] else 3


if __name__ == "__main__":
    raise SystemExit(main())

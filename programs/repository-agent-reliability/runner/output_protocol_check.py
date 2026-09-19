from __future__ import annotations

import hashlib
from pathlib import Path
import sys


RUNNER_ROOT = Path(__file__).resolve().parent

if str(RUNNER_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNNER_ROOT))

from engine import (
    build_prompt,
    candidate_admission,
    candidate_source_from_response,
    load_runtime,
)


EXPECTED_AP004_V1_PROTOCOL_SHA = (
    "40a847eb70d97273b99d3d442856854e"
    "a8c5002db11e04e6147faa503af33d1c"
)
EXPECTED_AP004_V1_PROMPT_SHA = (
    "e1e501736ccb7d78bbbdb0b8db2a54d1"
    "7e0eaea4577d7ff70b79ad10dce54cb0"
)


def expect_rejected(
    response: str,
    config: dict,
    reason_fragment: str,
) -> bool:
    try:
        candidate_source_from_response(
            response,
            config,
            "strict-code-only-v2",
        )
    except ValueError as exc:
        return reason_fragment in str(exc)
    return False


def main() -> int:
    task_root, config = load_runtime("AP-004")

    reference = (
        task_root
        / "controls"
        / "reference"
        / config["candidate_path"]
    ).read_text(encoding="utf-8")

    v1_prompt, _, v1_protocol = build_prompt(
        task_root,
        config,
        output_protocol="strict-code-only-v1",
    )
    v2_prompt, _, v2_protocol = build_prompt(
        task_root,
        config,
        output_protocol="strict-code-only-v2",
    )
    none_prompt, _, none_protocol = build_prompt(
        task_root,
        config,
        strict_code_only=False,
    )

    raw_v2 = candidate_source_from_response(
        reference,
        config,
        "strict-code-only-v2",
    )
    raw_v2_admission = candidate_admission(
        raw_v2,
        config["admission"],
    )

    fenced = "```python\n" + reference.rstrip() + "\n```\n"
    v1_fenced = candidate_source_from_response(
        fenced,
        config,
        "strict-code-only-v1",
    )
    v1_fenced_admission = candidate_admission(
        v1_fenced,
        config["admission"],
    )

    checks = {
        "v1_protocol_hash_unchanged": (
            v1_protocol["sha256"]
            == EXPECTED_AP004_V1_PROTOCOL_SHA
        ),
        "v1_prompt_hash_unchanged": (
            hashlib.sha256(
                v1_prompt.encode("utf-8")
            ).hexdigest()
            == EXPECTED_AP004_V1_PROMPT_SHA
        ),
        "v2_protocol_named": (
            v2_protocol["name"] == "strict-code-only-v2"
        ),
        "v2_protocol_differs_from_v1": (
            v2_protocol["sha256"] != v1_protocol["sha256"]
            and v2_prompt != v1_prompt
        ),
        "v2_raw_reference_admitted": (
            raw_v2_admission["accepted"] is True
        ),
        "v2_complete_fence_rejected": expect_rejected(
            fenced,
            config,
            "forbids Markdown code fences",
        ),
        "v2_unterminated_fence_rejected": expect_rejected(
            "```python\n" + reference.rstrip(),
            config,
            "forbids Markdown code fences",
        ),
        "v2_prose_prefix_rejected": expect_rejected(
            "Here is the fixed file:\n" + reference,
            config,
            "must begin with exactly",
        ),
        "v1_complete_fence_still_admitted": (
            v1_fenced_admission["accepted"] is True
        ),
        "legacy_none_mapping_preserved": (
            none_protocol["name"] == "none"
            and "RARB MACHINE OUTPUT PROTOCOL"
            not in none_prompt
        ),
    }

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'FAIL'}")

    print("v1_protocol_sha256:", v1_protocol["sha256"])
    print("v2_protocol_sha256:", v2_protocol["sha256"])
    print(
        "v2_prompt_sha256:",
        hashlib.sha256(v2_prompt.encode("utf-8")).hexdigest(),
    )

    ok = all(checks.values())
    print(
        "PHASE 8C INITIAL OUTPUT PROTOCOL GREEN"
        if ok
        else "PHASE 8C INITIAL OUTPUT PROTOCOL FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

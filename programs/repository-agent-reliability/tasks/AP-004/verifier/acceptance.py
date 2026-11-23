from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "runner"))
from candidate_proxy import remote_class

import sys


TASK_ID = "AP-004"
TASK_VERSION = "0.1.0"
VERIFIER_VERSION = "0.2.0"
PUBLIC_KEYS = {"id", "name", "email", "nickname"}


def load_builder(root: Path):
    return remote_class(root, "AP-004")


def gate(gate_id: str, passed: bool, diagnostic: str) -> dict:
    return {
        "id": gate_id,
        "passed": bool(passed),
        "diagnostic": diagnostic,
    }


def exact_int(value) -> bool:
    return type(value) is int


def evaluate(root: Path) -> dict:
    UserResponseBuilder = load_builder(root)

    normal_user = {
        "id": 7,
        "name": "Ada",
        "email": "ada@example.test",
        "nickname": "ada",
        "password_hash": "secret-hash",
        "internal_notes": "staff-only",
    }

    builder = UserResponseBuilder()
    status, body = builder.build(normal_user)

    g01 = type(status) is int and status == 200

    g02 = (
        isinstance(body, dict)
        and all(key in body for key in PUBLIC_KEYS)
        and exact_int(body.get("id"))
        and isinstance(body.get("name"), str)
        and isinstance(body.get("email"), str)
        and isinstance(body.get("nickname"), str)
    )

    missing_nickname_user = {
        "id": 8,
        "name": "Grace",
        "email": "grace@example.test",
        "password_hash": "another-secret",
    }
    explicit_null_user = {
        "id": 9,
        "name": "Lin",
        "email": "lin@example.test",
        "nickname": None,
        "password_hash": "third-secret",
    }

    missing_status, missing_body = UserResponseBuilder().build(missing_nickname_user)
    null_status, null_body = UserResponseBuilder().build(explicit_null_user)

    g03 = (
        isinstance(missing_body, dict)
        and "nickname" in missing_body
        and missing_body["nickname"] is None
        and isinstance(null_body, dict)
        and "nickname" in null_body
        and null_body["nickname"] is None
    )

    g04 = isinstance(body, dict) and set(body) == PUBLIC_KEYS

    for response_status, response_body, expected in (
        (status, body, normal_user),
        (missing_status, missing_body, missing_nickname_user),
        (null_status, null_body, explicit_null_user),
    ):
        g01 = g01 and type(response_status) is int and response_status == 200
        g02 = g02 and isinstance(response_body, dict) and all(
            type(response_body.get(key)) is type(expected.get(key))
            and response_body.get(key) == expected.get(key) for key in PUBLIC_KEYS
        )
        g04 = g04 and isinstance(response_body, dict) and set(response_body) == PUBLIC_KEYS

    gates = [
        gate(
            "AP004-G01",
            g01,
            "response status is exact integer 200"
            if g01
            else "response status changed from exact integer 200",
        ),
        gate(
            "AP004-G02",
            g02,
            "required public field names and types are stable"
            if g02
            else "required public field names or types changed",
        ),
        gate(
            "AP004-G03",
            g03,
            "nullable nickname remains present as None"
            if g03
            else "nullable nickname presence/null behavior changed",
        ),
        gate(
            "AP004-G04",
            g04,
            "public response contains no internal or extra fields"
            if g04
            else "public response leaked or added non-contract fields",
        ),
    ]

    status_value = (
        "VERIFIED_PASS"
        if all(item["passed"] for item in gates)
        else "VERIFIED_FAIL"
    )

    return {
        "task_id": TASK_ID,
        "task_version": TASK_VERSION,
        "verifier_version": VERIFIER_VERSION,
        "candidate": str(root),
        "gates": gates,
        "status": status_value,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = evaluate(args.candidate.resolve())

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(
            f"{result['status']}  "
            f"task={TASK_ID} verifier={VERIFIER_VERSION}"
        )
        for item in result["gates"]:
            label = "PASS" if item["passed"] else "FAIL"
            print(
                f"  {item['id']}: {label} - "
                f"{item['diagnostic']}"
            )

    return 0 if result["status"] == "VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

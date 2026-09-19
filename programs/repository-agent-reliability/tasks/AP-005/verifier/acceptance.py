from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys


TASK_ID = "AP-005"
TASK_VERSION = "0.1.0"
VERIFIER_VERSION = "0.1.0"
PUBLIC_KEYS = {"id", "value", "active", "note"}


def load_transformer(root: Path):
    source = root / "app" / "record_transformer.py"
    if not source.is_file():
        raise FileNotFoundError(f"Missing candidate source: {source}")

    spec = importlib.util.spec_from_file_location(
        "rarb_ap005_candidate",
        source,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load candidate: {source}")

    module = importlib.util.module_from_spec(spec)
    sys.modules.pop("rarb_ap005_candidate", None)
    spec.loader.exec_module(module)

    if not hasattr(module, "RecordTransformer"):
        raise RuntimeError("Candidate does not define RecordTransformer")

    return module.RecordTransformer


def gate(gate_id: str, passed: bool, diagnostic: str) -> dict:
    return {
        "id": gate_id,
        "passed": bool(passed),
        "diagnostic": diagnostic,
    }


def evaluate(root: Path) -> dict:
    RecordTransformer = load_transformer(root)

    rows = [
        {
            "id": "dup",
            "value": 0,
            "active": False,
            "note": "",
            "internal_tag": "do-not-copy",
        },
        {
            "id": "dup",
            "value": -2,
            "active": True,
            "internal_tag": "missing-note",
        },
        {
            "id": "b",
            "value": 3,
            "active": True,
            "note": None,
            "internal_tag": "explicit-null",
        },
    ]

    before = copy.deepcopy(rows)
    result = RecordTransformer().transform(rows)

    g01 = (
        isinstance(result, list)
        and len(result) == 3
        and all(isinstance(item, dict) for item in result)
        and [item.get("id") for item in result] == ["dup", "dup", "b"]
    )

    expected_values = [0, -2, 3]
    expected_active = [False, True, True]

    g02 = (
        isinstance(result, list)
        and len(result) == 3
        and all(type(item.get("id")) is str for item in result)
        and all(
            type(item.get("value")) is int
            and item.get("value") == expected
            for item, expected in zip(result, expected_values)
        )
        and all(
            type(item.get("active")) is bool
            and item.get("active") is expected
            for item, expected in zip(result, expected_active)
        )
    )

    g03 = (
        isinstance(result, list)
        and len(result) == 3
        and all("note" in item for item in result)
        and result[0]["note"] == ""
        and result[1]["note"] is None
        and result[2]["note"] is None
    )

    g04 = (
        rows == before
        and isinstance(result, list)
        and len(result) == 3
        and all(set(item) == PUBLIC_KEYS for item in result)
    )

    gates = [
        gate(
            "AP005-G01",
            g01,
            "row cardinality/order and duplicate identifiers are preserved"
            if g01
            else "row cardinality/order or duplicate identifier preservation changed",
        ),
        gate(
            "AP005-G02",
            g02,
            "integer and boolean values preserve exact values and types"
            if g02
            else "integer/boolean edge-case values or types changed",
        ),
        gate(
            "AP005-G03",
            g03,
            "missing, empty-string, and explicit-null note semantics are preserved"
            if g03
            else "optional note semantics collapsed distinct states",
        ),
        gate(
            "AP005-G04",
            g04,
            "source rows are unchanged and outputs expose exactly public fields"
            if g04
            else "source rows were mutated or output field surface changed",
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

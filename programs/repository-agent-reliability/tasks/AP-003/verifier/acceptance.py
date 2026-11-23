from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "runner"))
from candidate_proxy import remote_class

import sys

TASK_ID = "AP-003"
TASK_VERSION = "0.1.0"
VERIFIER_VERSION = "0.2.0"


def load_processor(root: Path):
    return remote_class(root, "AP-003")


def gate(gate_id: str, passed: bool, diagnostic: str) -> dict:
    return {"id": gate_id, "passed": bool(passed), "diagnostic": diagnostic}


def evaluate(root: Path) -> dict:
    EventProcessor = load_processor(root)

    p1 = EventProcessor()
    first = p1.handle("evt-1", 10)
    g01 = first is True and p1.total == 10

    p2 = EventProcessor()
    first_dup = p2.handle("evt-1", 10)
    second_dup = p2.handle("evt-1", 10)
    g02 = first_dup is True and second_dup is False and p2.total == 10

    p3 = EventProcessor()
    first_same_amount = p3.handle("evt-1", 10)
    second_same_amount = p3.handle("evt-2", 10)
    g03 = first_same_amount is True and second_same_amount is True and p3.total == 20

    p4 = EventProcessor()
    first_changed = p4.handle("evt-1", 10)
    changed_retry = p4.handle("evt-1", 99)
    g04 = first_changed is True and changed_retry is False and p4.total == 10

    # An old ID must remain deduplicated after other IDs have been handled.
    for retry_amount in (10, 99):
        interleaved = EventProcessor()
        first = interleaved.handle("old", 10)
        second = interleaved.handle("new", 10)
        retry = interleaved.handle("old", retry_amount)
        g04 = g04 and first is True and second is True and retry is False and interleaved.total == 20

    gates = [
        gate("AP003-G01", g01, "first delivery applied exactly once" if g01 else "first delivery behavior is incorrect"),
        gate("AP003-G02", g02, "exact duplicate delivery was ignored" if g02 else "exact duplicate delivery applied another side effect"),
        gate("AP003-G03", g03, "distinct event IDs with identical amounts both applied" if g03 else "deduplication incorrectly used payload/amount instead of event_id"),
        gate("AP003-G04", g04, "changed-payload retry with same event_id was ignored" if g04 else "same event_id with changed payload bypassed idempotency"),
    ]
    status = "VERIFIED_PASS" if all(item["passed"] for item in gates) else "VERIFIED_FAIL"
    return {
        "task_id": TASK_ID,
        "task_version": TASK_VERSION,
        "verifier_version": VERIFIER_VERSION,
        "candidate": str(root),
        "gates": gates,
        "status": status,
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
        print(f"{result['status']}  task={TASK_ID} verifier={VERIFIER_VERSION}")
        for item in result["gates"]:
            label = "PASS" if item["passed"] else "FAIL"
            print(f"  {item['id']}: {label} - {item['diagnostic']}")
    return 0 if result["status"] == "VERIFIED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

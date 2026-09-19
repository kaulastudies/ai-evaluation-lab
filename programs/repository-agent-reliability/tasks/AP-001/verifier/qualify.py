from __future__ import annotations

import json
from pathlib import Path
import sys

from acceptance import VERIFIER_VERSION, evaluate


TASK_ROOT = Path(__file__).resolve().parents[1]


def check_candidate(name, root, expected_pass):
    result = evaluate(root)
    actual_pass = result["status"] == "VERIFIED_PASS"
    return {
        "name": name,
        "candidate": root.relative_to(TASK_ROOT).as_posix(),
        "expected": "PASS" if expected_pass else "FAIL",
        "actual": "PASS" if actual_pass else "FAIL",
        "expectation_met": actual_pass == expected_pass,
        "failed_gates": [g["id"] for g in result["gates"] if not g["passed"]],
    }


def main():
    controls = [
        check_candidate("reference", TASK_ROOT / "controls" / "reference", True),
        check_candidate("known_bad", TASK_ROOT / "controls" / "known_bad", False),
        check_candidate(
            "mutation_remove_guard",
            TASK_ROOT / "controls" / "mutations" / "remove_guard",
            False,
        ),
        check_candidate(
            "mutation_invert_guard",
            TASK_ROOT / "controls" / "mutations" / "invert_guard",
            False,
        ),
        check_candidate(
            "mutation_wrong_generation",
            TASK_ROOT / "controls" / "mutations" / "wrong_generation",
            False,
        ),
    ]

    critical_mutations = [c for c in controls if c["name"].startswith("mutation_")]
    qualified = all(c["expectation_met"] for c in controls)

    record = {
        "task_id": "AP-001",
        "task_version": "0.1.0",
        "verifier_version": VERIFIER_VERSION,
        "reference_passed": controls[0]["actual"] == "PASS",
        "known_bad_rejected": controls[1]["actual"] == "FAIL",
        "critical_mutations_total": len(critical_mutations),
        "critical_mutations_rejected": sum(c["actual"] == "FAIL" for c in critical_mutations),
        "controls": controls,
        "status": "QUALIFIED" if qualified else "HOLD",
    }

    output = TASK_ROOT / "evidence" / "verifier-qualification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(json.dumps(record, indent=2))
    print(f"\nWrote {output}")

    return 0 if qualified else 1


if __name__ == "__main__":
    raise SystemExit(main())

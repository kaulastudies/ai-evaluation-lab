from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


TASK_ROOT = Path(__file__).resolve().parents[1]
VERIFIER = TASK_ROOT / "verifier" / "acceptance.py"
OUTPUT = TASK_ROOT / "evidence" / "verifier-qualification.json"

CONTROLS = [
    (
        "reference",
        TASK_ROOT / "controls" / "reference",
        "PASS",
    ),
    (
        "known_bad",
        TASK_ROOT / "controls" / "known_bad",
        "FAIL",
    ),
    (
        "mutation_drop_inactive",
        TASK_ROOT / "controls" / "mutations" / "drop_inactive",
        "FAIL",
    ),
    (
        "mutation_coerce_zero",
        TASK_ROOT / "controls" / "mutations" / "coerce_zero",
        "FAIL",
    ),
    (
        "mutation_collapse_empty_note",
        TASK_ROOT / "controls" / "mutations" / "collapse_empty_note",
        "FAIL",
    ),
    (
        "mutation_mutate_input",
        TASK_ROOT / "controls" / "mutations" / "mutate_input",
        "FAIL",
    ),
]


def run_control(name: str, root: Path, expected: str) -> dict:
    process = subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            str(root),
            "--json",
        ],
        cwd=TASK_ROOT,
        text=True,
        capture_output=True,
    )

    if not process.stdout.strip():
        raise RuntimeError(
            f"{name}: verifier produced no JSON\n"
            f"stderr:\n{process.stderr}"
        )

    result = json.loads(process.stdout)
    actual = (
        "PASS"
        if result["status"] == "VERIFIED_PASS"
        else "FAIL"
    )

    return {
        "name": name,
        "candidate": root.relative_to(TASK_ROOT).as_posix(),
        "expected": expected,
        "actual": actual,
        "expectation_met": actual == expected,
        "failed_gates": [
            item["id"]
            for item in result["gates"]
            if not item["passed"]
        ],
    }


def main() -> int:
    controls = [
        run_control(name, root, expected)
        for name, root, expected in CONTROLS
    ]
    mutations = controls[2:]

    record = {
        "task_id": "AP-005",
        "task_version": "0.1.0",
        "verifier_version": "0.1.0",
        "reference_passed": controls[0]["actual"] == "PASS",
        "known_bad_rejected": controls[1]["actual"] == "FAIL",
        "critical_mutations_total": len(mutations),
        "critical_mutations_rejected": sum(
            1 for item in mutations if item["actual"] == "FAIL"
        ),
        "controls": controls,
    }

    record["status"] = (
        "QUALIFIED"
        if record["reference_passed"]
        and record["known_bad_rejected"]
        and record["critical_mutations_rejected"]
        == record["critical_mutations_total"]
        and all(item["expectation_met"] for item in controls)
        else "HOLD"
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(record, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    print(json.dumps(record, indent=2))
    print()
    print(f"Wrote {OUTPUT}")

    return 0 if record["status"] == "QUALIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

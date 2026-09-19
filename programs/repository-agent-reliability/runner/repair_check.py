from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


RUNNER_ROOT = Path(__file__).resolve().parent
PROGRAM_ROOT = RUNNER_ROOT.parent
TASK_ROOT = PROGRAM_ROOT / "tasks" / "AP-003"
REPAIR = RUNNER_ROOT / "repair.py"
PARENT = (
    TASK_ROOT
    / "evidence"
    / "live"
    / "ap003-ollama-llama3-001"
)
REFERENCE = (
    TASK_ROOT
    / "controls"
    / "reference"
    / "app"
    / "event_processor.py"
)


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="rarb-repair-check-"
    ) as td:
        temp = Path(td)
        out = temp / "repair.json"
        response = temp / "response.txt"
        candidate = temp / "candidate.py"

        process = subprocess.run(
            [
                sys.executable,
                str(REPAIR),
                "--task",
                "AP-003",
                "--parent-evidence",
                str(PARENT),
                "--provider",
                "mock",
                "--response-file",
                str(REFERENCE),
                "--label",
                "ap003-mock-repair-check",
                "--response-out",
                str(response),
                "--candidate-out",
                str(candidate),
                "--out",
                str(out),
            ],
            cwd=PROGRAM_ROOT,
            text=True,
            capture_output=True,
        )

        if process.stdout:
            print(process.stdout.strip())
        if process.stderr:
            print(process.stderr, file=sys.stderr)

        if process.returncode != 0:
            print("PHASE 5A BOUNDED REPAIR FAILED")
            return 1

        record = json.loads(out.read_text(encoding="utf-8"))

        expected_parent_hash = (
            "934c5f633d9d37bd55e6dddbaf73903f"
            "ea16669fcc6c6acc0fa586c795dd325d"
        )

        failed_ids = record["repair_context"]["failed_gate_ids"]

        ok = (
            record["attempt_kind"] == "repair"
            and record["parent"]["record_hash"]
            == expected_parent_hash
            and failed_ids == ["AP003-G02", "AP003-G04"]
            and record["candidate_admission"]["accepted"] is True
            and record["evaluation"]["public_validation"]["passed"] is True
            and record["evaluation"]["verifier_qualification"]["status"]
            == "QUALIFIED"
            and record["evaluation"]["final_verdict"]
            == "VERIFIED_PASS"
            and record["evaluation"][
                "trusted_files_unchanged_after_scoring"
            ]
            is True
            and record["repair_conversion"] is True
            and record["final_verdict"] == "VERIFIED_PASS"
        )

        print(
            "PHASE 5A BOUNDED REPAIR GREEN"
            if ok
            else "PHASE 5A BOUNDED REPAIR FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

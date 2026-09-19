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


def run_case(response_file: Path, label: str, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
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
            str(response_file),
            "--output-protocol",
            "strict-code-only-v2",
            "--label",
            label,
            "--out",
            str(out),
        ],
        cwd=PROGRAM_ROOT,
        text=True,
        capture_output=True,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(
        prefix="rarb-repair-protocol-v2-"
    ) as td:
        temp = Path(td)

        good_out = temp / "good.json"
        good = run_case(
            REFERENCE,
            "ap003-mock-repair-protocol-v2-good",
            good_out,
        )
        if good.stdout:
            print(good.stdout.strip())
        if good.stderr:
            print(good.stderr, file=sys.stderr)

        if good.returncode != 0:
            print("PHASE 5B FORMAT-RETRY PROTOCOL FAILED")
            return 1

        good_record = json.loads(good_out.read_text(encoding="utf-8"))

        fenced = temp / "fenced.txt"
        fenced.write_text(
            "```python\n"
            + REFERENCE.read_text(encoding="utf-8").rstrip()
            + "\n```\n",
            encoding="utf-8",
            newline="\n",
        )

        bad_out = temp / "bad.json"
        bad = run_case(
            fenced,
            "ap003-mock-repair-protocol-v2-fenced",
            bad_out,
        )
        if bad.stdout:
            print(bad.stdout.strip())
        if bad.stderr:
            print(bad.stderr, file=sys.stderr)

        bad_record = json.loads(bad_out.read_text(encoding="utf-8"))

        ok = (
            good_record["output_protocol"]["name"]
            == "strict-code-only-v2"
            and good_record["repair_context"]["failed_gate_ids"]
            == ["AP003-G02", "AP003-G04"]
            and good_record["candidate_admission"]["accepted"] is True
            and good_record["evaluation"]["verification"]["status"]
            == "VERIFIED_PASS"
            and good_record["repair_conversion"] is True
            and good_record["final_verdict"] == "VERIFIED_PASS"
            and bad.returncode == 2
            and bad_record["candidate_admission"]["accepted"] is False
            and "forbids backtick" in bad_record["candidate_admission"]["reason"]
            and bad_record["evaluation"] is None
            and bad_record["final_verdict"] == "HOLD"
        )

        print(
            "PHASE 5B FORMAT-RETRY PROTOCOL GREEN"
            if ok
            else "PHASE 5B FORMAT-RETRY PROTOCOL FAILED"
        )
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER_DIR = Path(__file__).resolve().parent
PROTOCOL_TRIAL = RUNNER_DIR / "protocol_model_trial.py"
ADMISSION_REPLAY_CHECK = RUNNER_DIR / "admission_replay_check.py"


def run_mock(
    name: str,
    response_file: Path,
    expected_rc: int,
    expected_verdict: str,
    expected_admitted: bool,
) -> bool:
    with tempfile.TemporaryDirectory(prefix="rarb-protocol-check-") as td:
        temp = Path(td)
        out = temp / f"{name}.json"

        process = subprocess.run(
            [
                sys.executable,
                str(PROTOCOL_TRIAL),
                "--provider",
                "mock",
                "--response-file",
                str(response_file),
                "--output-protocol",
                "strict-code-only-v1",
                "--label",
                name,
                "--out",
                str(out),
            ],
            cwd=TASK_ROOT,
            text=True,
            capture_output=True,
        )

        if process.returncode != expected_rc:
            print(process.stdout)
            print(process.stderr, file=sys.stderr)
            return False

        record = json.loads(out.read_text(encoding="utf-8"))
        ok = (
            record["output_protocol"]["name"] == "strict-code-only-v1"
            and record["output_protocol"]["sha256"]
            and record["candidate_admission"]["accepted"] is expected_admitted
            and record["final_verdict"] == expected_verdict
        )

        print(
            f"{name}: protocol={record['output_protocol']['name']} "
            f"admitted={record['candidate_admission']['accepted']} "
            f"verdict={record['final_verdict']}"
        )
        return bool(ok)


def main() -> int:
    reference = (
        TASK_ROOT
        / "controls"
        / "reference"
        / "app"
        / "resource_view.py"
    )

    with tempfile.TemporaryDirectory(prefix="rarb-protocol-prose-") as td:
        mixed = Path(td) / "mixed.txt"
        mixed.write_text(
            "Here is the fix:\n```python\n"
            + reference.read_text(encoding="utf-8")
            + "```\nThis fixes the issue.\n",
            encoding="utf-8",
            newline="\n",
        )

        good_ok = run_mock(
            "protocol-reference",
            reference,
            0,
            "VERIFIED_PASS",
            True,
        )
        strict_ok = run_mock(
            "protocol-mixed-prose",
            mixed,
            2,
            "HOLD",
            False,
        )

    replay = subprocess.run(
        [sys.executable, str(ADMISSION_REPLAY_CHECK)],
        cwd=TASK_ROOT,
        text=True,
        capture_output=True,
    )
    print(replay.stdout.strip())
    if replay.returncode != 0:
        print(replay.stderr, file=sys.stderr)

    historical_ok = (
        replay.returncode == 0
        and "PHASE 3C ADMISSION REPLAY GREEN" in replay.stdout
    )

    ok = good_ok and strict_ok and historical_ok
    print(
        "PHASE 3D OUTPUT PROTOCOL GREEN"
        if ok
        else "PHASE 3D OUTPUT PROTOCOL FAILED"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

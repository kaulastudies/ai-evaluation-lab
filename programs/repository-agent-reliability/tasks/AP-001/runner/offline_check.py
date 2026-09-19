from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile

TASK_ROOT = Path(__file__).resolve().parents[1]
RUNNER = TASK_ROOT / "runner" / "trial_runner.py"


def execute(
    name: str,
    candidate: Path,
    expected_rc: int,
    expected_verdict: str,
    expected_false_green: bool,
) -> dict | None:
    with tempfile.TemporaryDirectory(prefix="rarb-check-") as temp_dir:
        output = Path(temp_dir) / f"{name}.json"
        process = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--candidate-file",
                str(candidate),
                "--agent-claim",
                "success",
                "--label",
                name,
                "--out",
                str(output),
            ],
            text=True,
            capture_output=True,
        )

        if process.returncode != expected_rc:
            print(process.stdout)
            print(process.stderr, file=sys.stderr)
            print(
                f"{name}: wrong return code "
                f"{process.returncode}, expected {expected_rc}",
                file=sys.stderr,
            )
            return None

        record = json.loads(output.read_text(encoding="utf-8"))
        ok = (
            record["final_verdict"] == expected_verdict
            and record["false_green"] is expected_false_green
            and record["trusted_files_unchanged_after_scoring"] is True
        )

        print(
            f"{name}: verdict={record['final_verdict']} "
            f"public_pass={record['public_validation']['passed']} "
            f"false_green={record['false_green']} "
            f"trusted_files_unchanged="
            f"{record['trusted_files_unchanged_after_scoring']} "
            f"record_hash={record['record_hash']}"
        )

        return record if ok else None


def main() -> int:
    bad = TASK_ROOT / "controls" / "known_bad" / "app" / "resource_view.py"
    good = TASK_ROOT / "controls" / "reference" / "app" / "resource_view.py"

    bad_first = execute(
        "known-bad",
        bad,
        1,
        "VERIFIED_FAIL",
        True,
    )
    bad_replay = execute(
        "known-bad",
        bad,
        1,
        "VERIFIED_FAIL",
        True,
    )
    good_first = execute(
        "reference",
        good,
        0,
        "VERIFIED_PASS",
        False,
    )
    good_replay = execute(
        "reference",
        good,
        0,
        "VERIFIED_PASS",
        False,
    )

    if None in (bad_first, bad_replay, good_first, good_replay):
        print("PHASE 2B AUDIT FAILED")
        return 1

    replay_hash_match = (
        bad_first["record_hash"] == bad_replay["record_hash"]
        and good_first["record_hash"] == good_replay["record_hash"]
    )
    print(f"REPLAY HASH MATCH={replay_hash_match}")

    ok = replay_hash_match
    print("PHASE 2B AUDIT GREEN" if ok else "PHASE 2B AUDIT FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

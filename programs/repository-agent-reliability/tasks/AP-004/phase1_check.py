from __future__ import annotations

from pathlib import Path
import subprocess
import sys


TASK_ROOT = Path(__file__).resolve().parent


def run(command: list[str], cwd: Path, expected: int) -> None:
    process = subprocess.run(command, cwd=cwd)
    if process.returncode != expected:
        raise SystemExit(
            f"Command returned {process.returncode}, "
            f"expected {expected}: "
            + " ".join(command)
        )


def main() -> int:
    print("=== 1/4 Public tests on vulnerable fixture (must PASS) ===")
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests/public",
            "-v",
        ],
        TASK_ROOT / "fixture",
        0,
    )

    print()
    print("=== 2/4 Qualified verifier on vulnerable fixture (must FAIL) ===")
    run(
        [
            sys.executable,
            str(TASK_ROOT / "verifier" / "acceptance.py"),
            str(TASK_ROOT / "fixture"),
        ],
        TASK_ROOT,
        1,
    )

    print()
    print("=== 3/4 Verifier qualification controls (must QUALIFY) ===")
    run(
        [
            sys.executable,
            str(TASK_ROOT / "verifier" / "qualify.py"),
        ],
        TASK_ROOT,
        0,
    )

    print()
    print("=== 4/4 Qualified verifier on reference control (must PASS) ===")
    run(
        [
            sys.executable,
            str(TASK_ROOT / "verifier" / "acceptance.py"),
            str(TASK_ROOT / "controls" / "reference"),
        ],
        TASK_ROOT,
        0,
    )

    print()
    print("AP-004 PHASE 1 GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


TASK_ROOT = Path(__file__).resolve().parent


def run(label, command, cwd=None, expected=0):
    print(f"\n=== {label} ===", flush=True)
    proc = subprocess.run(command, cwd=cwd, text=True)
    if proc.returncode != expected:
        print(
            f"\nERROR: {label} returned {proc.returncode}; expected {expected}.",
            file=sys.stderr,
        )
        return False
    return True


def main():
    python = sys.executable

    ok = run(
        "1/4 Public tests on vulnerable fixture (must PASS)",
        [python, "-m", "unittest", "discover", "-s", "tests/public", "-v"],
        cwd=TASK_ROOT / "fixture",
        expected=0,
    )

    ok = run(
        "2/4 Qualified verifier on vulnerable fixture (must FAIL)",
        [python, str(TASK_ROOT / "verifier" / "acceptance.py"), str(TASK_ROOT / "fixture")],
        expected=1,
    ) and ok

    ok = run(
        "3/4 Verifier qualification controls (must QUALIFY)",
        [python, str(TASK_ROOT / "verifier" / "qualify.py")],
        expected=0,
    ) and ok

    ok = run(
        "4/4 Qualified verifier on reference control (must PASS)",
        [
            python,
            str(TASK_ROOT / "verifier" / "acceptance.py"),
            str(TASK_ROOT / "controls" / "reference"),
        ],
        expected=0,
    ) and ok

    print("\n" + ("PHASE 1 GREEN" if ok else "PHASE 1 FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

def run_tests(test_file: Path, router_file: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["ROUTER_PATH"] = str(router_file)
    return subprocess.run(
        [sys.executable, str(test_file)],
        env=env,
        text=True,
        capture_output=True,
    )

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_dir")
    args = parser.parse_args()
    root = Path(args.task_dir).resolve()

    broken = root / "environment" / "router.py"
    reference = root / "solution" / "router_reference.py"
    tests = root / "tests" / "test_router.py"

    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "router.py"

        shutil.copy2(broken, work)
        bad = run_tests(tests, work)
        if bad.returncode == 0:
            print(bad.stdout)
            raise SystemExit("BLOCKER: intentionally broken router unexpectedly passed")

        shutil.copy2(reference, work)
        good = run_tests(tests, work)
        if good.returncode != 0:
            print(good.stdout)
            print(good.stderr)
            raise SystemExit("BLOCKER: reference router failed")

    print("PASS: broken candidate rejected; reference solution accepted")

if __name__ == "__main__":
    main()

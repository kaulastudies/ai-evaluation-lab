"""Show the retained-receipt regression fails before and passes after the patch.

Uses only synthetic temporary files and mocked subprocesses. Does not install
libraries, start model processes, access a real stage, or change upstream source.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from .fixtures import HERE, verify_source


def validate(source):
    lock = verify_source(source)
    prefix = Path("integrations/ai-evaluation-lab")
    with tempfile.TemporaryDirectory(prefix="eo-patch-check-") as temporary:
        root = Path(temporary)
        (root / prefix).mkdir(parents=True)
        for name in ("accept-sovereign-inference.py", "accept-sovereign-inference.test.py"):
            shutil.copyfile(source / prefix / name, root / prefix / name)
        subprocess.run(["git", "apply", "--check", str(HERE / "sovereign-blocked-receipt.patch")], cwd=root, check=True)
        subprocess.run(["git", "apply", str(HERE / "sovereign-blocked-receipt.patch")], cwd=root, check=True)
        patched = (root / prefix / "accept-sovereign-inference.py").read_bytes()
        # Retain the new regression test while temporarily restoring original code.
        shutil.copyfile(source / prefix / "accept-sovereign-inference.py", root / prefix / "accept-sovereign-inference.py")
        env = {k: os.environ[k] for k in ("PATH", "LANG", "LC_ALL") if k in os.environ}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        command = [sys.executable, "-B", str(root / prefix / "accept-sovereign-inference.test.py")]
        before = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=15)
        assert before.returncode == 1 and "blocked dependency must leave one receipt" in before.stderr, before.stderr
        (root / prefix / "accept-sovereign-inference.py").write_bytes(patched)
        after = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=15)
        assert after.returncode == 0 and "Ran 4 tests" in after.stderr, after.stderr
    return {"upstream_commit": lock["commit"], "synthetic_regression_only": True,
            "before_patch": {"exit_code": before.returncode, "output": before.stderr},
            "after_patch": {"exit_code": after.returncode, "output": after.stderr},
            "model_processes_started": 0, "host_packages_installed": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = validate(args.source.resolve())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Original: regression reproduced; patched: all 4 tests pass. No model or host changes.")


if __name__ == "__main__":
    main()

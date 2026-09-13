from __future__ import annotations

import argparse
import hashlib
import json
import tomllib
from pathlib import Path

REQUIRED = [
    "instruction.md",
    "task.toml",
    "environment/Dockerfile",
    "environment/router.py",
    "solution/solve.sh",
    "solution/router_reference.py",
    "tests/Dockerfile",
    "tests/test.sh",
    "tests/test_router.py",
]

def fail(message: str) -> None:
    print(f"BLOCKER: {message}")
    raise SystemExit(1)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("task_dir")
    args = parser.parse_args()

    root = Path(args.task_dir)
    if not root.is_dir():
        fail(f"task directory not found: {root}")

    for rel in REQUIRED:
        if not (root / rel).is_file():
            fail(f"missing required file: {rel}")

    with (root / "task.toml").open("rb") as handle:
        config = tomllib.load(handle)

    if str(config.get("schema_version")) != "1.0":
        fail("schema_version must be 1.0")

    task = config.get("task") or {}
    if not task.get("name"):
        fail("[task] requires name")

    verifier = config.get("verifier") or {}
    if verifier.get("environment_mode") != "separate":
        fail("verifier.environment_mode must be separate")

    verifier_env = verifier.get("environment") or {}
    if verifier_env.get("allow_internet") is not False:
        fail("verifier environment must set allow_internet = false")

    instruction = (root / "instruction.md").read_text(encoding="utf-8")
    if "LAB-CANARY:" not in instruction:
        fail("instruction.md must contain a LAB-CANARY marker")

    contract_material = b"".join([
        (root / "instruction.md").read_bytes(),
        (root / "task.toml").read_bytes(),
        (root / "tests" / "test_router.py").read_bytes(),
    ])
    contract_hash = hashlib.sha256(contract_material).hexdigest()

    print(json.dumps({
        "status": "PASS",
        "task": task["name"],
        "contract_hash": contract_hash,
    }, indent=2))

if __name__ == "__main__":
    main()

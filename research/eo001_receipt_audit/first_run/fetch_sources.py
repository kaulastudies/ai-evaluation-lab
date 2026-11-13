"""Fetch the six public files pinned for fixture and patch verification only."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
from .fixtures import HERE, verify_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    lock = json.loads((HERE / "source_lock.json").read_text())
    for name, expected in lock["files"].items():
        url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{name}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read(1048577)
        if len(data) > 1048576 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("SOURCE_HASH_MISMATCH: " + name)
        target = args.directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    verify_source(args.directory)
    print(f"Verified six source files at {lock['commit']}; nothing executed.")


if __name__ == "__main__":
    main()

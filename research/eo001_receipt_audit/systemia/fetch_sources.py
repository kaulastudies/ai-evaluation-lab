"""Fetch reviewed, hash-pinned public inputs to an external temporary directory."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent


def verify(directory):
    lock = json.loads((HERE / "source_lock.json").read_text())
    for name, expected in lock["files"].items():
        actual = hashlib.sha256((Path(directory) / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError("SOURCE_HASH_MISMATCH: " + name)
    return lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    lock = json.loads((HERE / "source_lock.json").read_text())
    for name, expected in lock["files"].items():
        target = args.directory / name
        url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{name}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("SOURCE_HASH_MISMATCH: " + name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    verify(args.directory)
    print(f"Verified {len(lock['files'])} source files at {lock['commit']}")


if __name__ == "__main__":
    main()

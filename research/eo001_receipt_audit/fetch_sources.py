"""Explicitly download two pinned public source files; never execute them here."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Temporary checkout directory outside the repository")
    args = parser.parse_args()
    pins = json.loads((HERE / "source_lock.json").read_text())
    names = {"forge": "ambiguous-external-effect.mjs", "inspect_intake": "adoption.py"}
    args.directory.mkdir(parents=True, exist_ok=True)
    for key, name in names.items():
        pin = pins[key]
        url = f"https://raw.githubusercontent.com/{pin['repository']}/{pin['commit']}/{pin['path']}"
        with urllib.request.urlopen(url, timeout=30) as response:
            data = response.read(1024 * 1024 + 1)
        if len(data) > 1024 * 1024 or hashlib.sha256(data).hexdigest() != pin["sha256"]:
            raise ValueError("pinned source bytes do not match: " + key)
        path = args.directory / name
        path.write_bytes(data)
        print(path)


if __name__ == "__main__":
    main()

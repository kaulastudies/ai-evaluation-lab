"""Install the pinned, hash-verified browser Python runtime; no Python packages."""
import hashlib
import json
from pathlib import Path
import urllib.request

HERE = Path(__file__).resolve().parent


def prepare():
    manifest = json.loads((HERE / "browser-runtime.json").read_text())
    root = HERE / "vendor/pyodide"
    root.mkdir(parents=True, exist_ok=True)
    for record in manifest["files"]:
        target = root / record["name"]
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == record["sha256"]:
            continue
        with urllib.request.urlopen(record["url"], timeout=90) as response:
            content = response.read()
        if len(content) != record["bytes"] or hashlib.sha256(content).hexdigest() != record["sha256"]:
            raise RuntimeError(f"Runtime integrity mismatch: {record['name']}")
        target.write_bytes(content)
    print(f"Browser Python runtime {manifest['version']} ready; all file hashes verified.")


if __name__ == "__main__":
    prepare()

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path("runs/local")
FILES = [
    ROOT / "inspect-llama3-baseline.json",
    ROOT / "harbor-oracle-route-policy.json",
]


def canonical(record: dict[str, Any]) -> str:
    return json.dumps(
        {k: v for k, v in record.items() if k != "record_hash"},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


for path in FILES:
    if not path.is_file():
        raise SystemExit(f"BLOCKER: missing local evidence record {path}")

    record = json.loads(path.read_text(encoding="utf-8"))

    expected = hashlib.sha256(canonical(record).encode("utf-8")).hexdigest()
    if record.get("record_hash") != expected:
        raise SystemExit(f"BLOCKER: invalid record hash in {path}")

    if record.get("final_label") != "PASS":
        raise SystemExit(f"BLOCKER: non-PASS record in {path}")

    if record.get("final_status") != "ACCEPTED":
        raise SystemExit(f"BLOCKER: non-ACCEPTED record in {path}")

print("PASS: local evidence records are accepted and hash-valid")

from __future__ import annotations
import hashlib, json, uuid
from datetime import datetime, timezone
from typing import Any

def utc_now() -> str: return datetime.now(timezone.utc).isoformat()
def canonical_payload(record: dict[str, Any]) -> str:
    return json.dumps({k:v for k,v in record.items() if k != "record_hash"}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
def hash_record(record: dict[str, Any]) -> str: return hashlib.sha256(canonical_payload(record).encode()).hexdigest()
def new_evaluation_id() -> str: return f"EV-{uuid.uuid4().hex[:12].upper()}"

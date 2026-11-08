#!/usr/bin/env python3
"""Offline verifier: no model, Docker, network or execution of supplied code."""
import argparse
import json
from pathlib import Path
from receiptops.audit import check
from receiptops.receipts import digest, verify

def verify_bundle(bundle: dict, trusted_key: str) -> dict:
    receipt = bundle["receipt"]
    if not verify(receipt, trusted_key.strip()):
        return {"passed": False, "reason": "Signature, hash or pinned public key mismatch."}
    payload = receipt["payload"]
    if payload["kind"] != "invoice_audit":
        return {"passed": False, "reason": "This verifier recomputes invoice audits only."}
    for field, raw in [("input_sha256", bundle["input_csv"]), ("code_sha256", bundle["code"]), ("stdout_sha256", bundle["stdout"])]:
        if digest(raw.encode()) != payload[field]:
            return {"passed": False, "reason": field + " mismatch."}
    candidate = json.loads(bundle["stdout"])
    validation = check(bundle["input_csv"], candidate)
    sandbox = payload["sandbox"]
    passed = validation["passed"] and payload["verification"]["passed"] is True and candidate == payload["result"] and sandbox["exit_code"] == 0 and sandbox["timed_out"] is False and sandbox["output_limited"] is False and sandbox["container_removed"] is True
    return {"passed": bool(passed), "run_id": payload["run_id"], "independent_recomputation": validation,
            "scope": "Authenticity, bound artifacts and result correctness. Execution provenance is attested by the signer, not independently proven."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--public-key", required=True, type=Path, help="A previously trusted key, obtained separately from the bundle")
    args = parser.parse_args()
    try:
        result = verify_bundle(json.loads(args.bundle.read_text()), args.public_key.read_text())
    except Exception as error:
        result = {"passed": False, "reason": "Malformed bundle: " + type(error).__name__}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)

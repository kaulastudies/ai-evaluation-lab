"""Offline planning check only: never executes or authorizes a model run."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from research.eo001_coordination.assess_report import load

FIELDS = {
    "lab_adapter_commit": 40, "forge_adapter_commit": 40,
    "model_sha256": 64, "runtime_sha256": 64,
    "prompt_sha256": 64, "context_serialization_sha256": 64,
    "warmup_prompt_sha256": 64,
}


def check(manifest):
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    problems = []
    if manifest.get("schema") != "EO001-RUN-PLAN/0.1.0":
        problems.append("schema")
    for key, length in FIELDS.items():
        value = manifest.get(key)
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{%d}" % length, value):
            problems.append(key)
    for key in ("context_serialization", "host_configuration", "output_naming", "cleanup_checks"):
        value = manifest.get(key)
        if not isinstance(value, str) or not value.strip():
            problems.append(key)
    for key in ("generation_parameters", "review_references"):
        value = manifest.get(key)
        if not isinstance(value, dict) or not value:
            problems.append(key)
    refs = manifest.get("review_references", {})
    if not isinstance(refs, dict) or any(
        not isinstance(refs.get(k), str) or not refs[k].strip() for k in ("lab", "evercraft")
    ):
        problems.append("review_references.lab_and_evercraft")
    for key in ("max_output_tokens", "warmup_timeout_seconds"):
        if type(manifest.get(key)) is not int or manifest[key] <= 0:
            problems.append(key)
    for key, expected in (("decision_timeout_seconds", 15), ("max_decisions_per_case", 6), ("warmup_requests", 1)):
        if type(manifest.get(key)) is not int or manifest[key] != expected:
            problems.append(key)
    if manifest.get("scenario_order") != ["none", "ack_loss", "lookup_outage", "tamper"]:
        problems.append("scenario_order")
    if manifest.get("stop_on_timeout") is not True or manifest.get("replace_failed_attempts") is not False:
        problems.append("failure_retention_policy")
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    return {
        "state": "NEEDS_REVIEW" if problems else "FIELDS_COMPLETE_REVIEW_REQUIRED",
        "unresolved_or_invalid_fields": sorted(set(problems)),
        "manifest_sha256": digest,
        "execution_authorized": False,
        "source_pins_or_review_authenticity_verified": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        result = check(load(args.manifest))
    except (ValueError, TypeError, OSError):
        print("INVALID_MANIFEST")
        return 2
    print(json.dumps(result, indent=2))
    return 2 if result["unresolved_or_invalid_fields"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

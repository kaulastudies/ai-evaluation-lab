"""Offline research adapters. Never executes agents or promotes external verdicts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MAX_BYTES = 16 * 1024 * 1024
MAX_SAMPLES = 10_000
ADAPTER_VERSION = "0.1.0"
INSPECT_INTERFACE_COMMIT = "2f78dcb29eb02830b4536050f61fd1a0f7665523"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class IntakeError(ValueError):
    """The supplied evidence cannot be represented without ambiguity."""


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise IntakeError("duplicate JSON object key")
        result[key] = value
    return result


def _constant(_: str) -> None:
    raise IntakeError("non-finite JSON number")


def _finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise IntakeError("non-finite JSON number")
    return number


def read_json(raw: bytes) -> Any:
    if len(raw) > MAX_BYTES:
        raise IntakeError("input exceeds the 16 MiB limit")
    try:
        text = raw.decode("utf-8")
        depth, in_string, escaped = 0, False, False
        for char in text:
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char in "[{":
                depth += 1
                if depth > 64:
                    raise IntakeError("JSON nesting exceeds 64 levels")
            elif char in "]}":
                depth -= 1
        return json.loads(text, object_pairs_hook=_pairs,
                          parse_constant=_constant, parse_float=_finite_float)
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise IntakeError("invalid or ambiguous JSON input") from exc


def read_bytes(path: Path) -> bytes:
    with path.open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise IntakeError("input exceeds the 16 MiB limit")
    return data


def canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise IntakeError("value cannot be represented as canonical JSON") from exc


def object_value(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise IntakeError(f"{name} must be an object")
    return value


def integer(value: Any, name: str, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= 1_000_000_000:
        raise IntakeError(f"{name} must be a bounded integer >= {minimum}")
    return value


def text_value(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise IntakeError(f"{name} must be nonempty text up to 1024 characters")
    return value


def score_value(value: Any, depth: int = 0) -> Any:
    """Preserve opaque upstream score values; never interpret 1 or C as PASS."""
    if depth > 8:
        raise IntakeError("score value nesting exceeds 8 levels")
    if type(value) in (int, float, bool) or value is None:
        if type(value) is float and not math.isfinite(value):
            raise IntakeError("non-finite score")
        return value
    if isinstance(value, str) and len(value) <= 4096:
        return value
    if isinstance(value, list) and len(value) <= 256:
        return [score_value(item, depth + 1) for item in value]
    if isinstance(value, dict) and len(value) <= 256:
        return {text_value(k, "score key"): score_value(v, depth + 1)
                for k, v in value.items()}
    raise IntakeError("unsupported or oversized score value")


def inspect_observations(raw: bytes, expected_sha256: str) -> dict[str, Any]:
    """Read a bounded Inspect v2 JSON export as unverified external observations.

    This is a deliberate subset adapter, not an EvalLog validator or .eval reader.
    All samples, scores, errors and incomplete-run indicators remain distinguishable.
    """
    if len(raw) > MAX_BYTES:
        raise IntakeError("input exceeds the 16 MiB limit")
    if not isinstance(expected_sha256, str) or not SHA256.fullmatch(expected_sha256):
        raise IntakeError("expected SHA-256 must be 64 lowercase hex characters")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha256:
        raise IntakeError("source SHA-256 does not match the supplied digest")
    log = object_value(read_json(raw), "log")
    if type(log.get("version")) is not int or log["version"] != 2:
        raise IntakeError("only Inspect JSON log version 2 is supported")
    status = log.get("status")
    if status not in ("started", "success", "cancelled", "error"):
        raise IntakeError("unknown Inspect execution status")
    spec = object_value(log.get("eval"), "eval")
    identity = {name: text_value(spec.get(name), f"eval.{name}")
                for name in ("task", "model", "created")}
    identity["run_id"] = spec.get("run_id") or None
    if identity["run_id"] is not None:
        text_value(identity["run_id"], "eval.run_id")
    task_version = spec.get("task_version", 0)
    if type(task_version) not in (int, str):
        raise IntakeError("task version must be an integer or text")
    identity["task_version"] = score_value(task_version)
    invalidated = log.get("invalidated", False)
    if type(invalidated) is not bool:
        raise IntakeError("invalidated must be boolean")
    samples = log.get("samples")
    if samples is None:
        samples = []
    if not isinstance(samples, list) or len(samples) > MAX_SAMPLES:
        raise IntakeError("samples must be an array with at most 10000 entries")
    observed, seen = [], set()
    for sample in samples:
        sample = object_value(sample, "sample")
        sid = sample.get("id")
        if type(sid) is int:
            integer(sid, "sample.id")
        elif isinstance(sid, str):
            text_value(sid, "sample.id")
        else:
            raise IntakeError("sample.id must be integer or nonempty text")
        epoch = integer(sample.get("epoch"), "sample.epoch", 1)
        key = canonical([sid, epoch])
        if key in seen:
            raise IntakeError("duplicate sample id and epoch")
        seen.add(key)
        scores = sample.get("scores")
        if scores is None:
            scores = {}
        scores = object_value(scores, "sample.scores")
        if len(scores) > 256:
            raise IntakeError("too many scorers in a sample")
        values = {}
        for name, score in scores.items():
            text_value(name, "scorer name")
            score = object_value(score, "score")
            if "value" not in score:
                raise IntakeError("score has no value")
            values[name] = score_value(score["value"])
        retries = sample.get("error_retries")
        if retries is not None and not isinstance(retries, list):
            raise IntakeError("error_retries must be an array or null")
        observed.append({"sample_id": sid, "epoch": epoch,
                         "upstream_scores": values,
                         "error_present": sample.get("error") is not None,
                         "invalidation_present": sample.get("invalidation") is not None,
                         "limit_present": sample.get("limit") is not None,
                         "retried_errors": len(retries or [])})
    reasons = []
    if status != "success":
        reasons.append("execution_not_success")
    if log.get("error") is not None:
        reasons.append("run_error_present")
    if invalidated or any(s["invalidation_present"] for s in observed):
        reasons.append("invalidation_present")
    if any(s["error_present"] for s in observed):
        reasons.append("sample_error_present")
    if any(s["limit_present"] for s in observed):
        reasons.append("sample_limit_present")
    if any(not s["upstream_scores"] for s in observed):
        reasons.append("unscored_samples_present")
    if not observed:
        reasons.append("sample_evidence_absent")
    results = log.get("results")
    declared: dict[str, Any] = {"total_samples": None, "completed_samples": None,
                                "logged_samples": None, "early_stopping_present": False}
    if results is None:
        reasons.append("results_absent")
    else:
        results = object_value(results, "results")
        for key in ("total_samples", "completed_samples", "logged_samples"):
            if results.get(key) is not None:
                declared[key] = integer(results[key], "results." + key)
        declared["early_stopping_present"] = results.get("early_stopping") is not None
        if declared["early_stopping_present"]:
            reasons.append("early_stopping_present")
    total, completed, logged = (declared[k] for k in
                                ("total_samples", "completed_samples", "logged_samples"))
    if total is None:
        reasons.append("planned_count_unavailable")
    else:
        if len(observed) > total or (completed is not None and completed > total) or (logged is not None and logged > total):
            raise IntakeError("sample counts exceed the declared total")
        if len(observed) != total:
            reasons.append("planned_samples_missing")
        if completed != total:
            reasons.append("declared_completion_incomplete")
        if logged is not None and logged != total:
            reasons.append("logged_count_incomplete")
    if identity["run_id"] is None:
        reasons.append("run_id_absent")
    report = {
        "schema_version": 1,
        "adapter_version": ADAPTER_VERSION,
        "reviewed_inspect_interface_commit": INSPECT_INTERFACE_COMMIT,
        "kind": "external-evaluation-observations",
        "evidence_state": "UNVERIFIED_EXTERNAL",
        "source_format": "inspect-json-v2",
        "source_sha256": digest,
        "source_bytes": len(raw),
        "claimed_identity": identity,
        "execution_status": status,
        "declared_counts": declared,
        "observed_sample_count": len(observed),
        "samples": observed,
        "incompleteness_reasons": sorted(set(reasons)),
        "lab_verdict": None,
        "promotion_allowed": False,
        "limitations": [
            "Digest equality binds bytes; it does not authenticate the runner or author.",
            "Upstream scores are not independently verified Lab verdicts.",
            "Task identity is a claim; no frozen AS/RARB contract is bound by this adapter.",
            "This subset does not validate full EvalLog semantics, raw traces or aggregate metrics.",
            "Inputs, answers, messages, arbitrary metadata and error text are omitted; identifiers and score values still require publication review."
        ],
    }
    report["report_sha256"] = hashlib.sha256(canonical(report)).hexdigest()
    return report


def check_catalogue(directory: Path = HERE) -> dict[str, Any]:
    catalogue = read_json(read_bytes(directory / "catalogue.json"))
    registry = read_json(read_bytes(directory / "sources.json"))
    entries, sources = catalogue["projects"], registry["sources"]
    if len(entries) != 125 or {x["id"] for x in entries} != set(range(1, 126)):
        raise IntakeError("catalogue must cover all 125 supplied entries exactly once")
    ids = {s["id"] for s in sources}
    if len(ids) != len(sources):
        raise IntakeError("duplicate source ID")
    for source in sources:
        if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
            raise IntakeError("source commit must be pinned")
        if source["license_spdx"] not in ("MIT", "Apache-2.0", "BSD-3-Clause"):
            raise IntakeError("source licence requires a separate review")
        if source["third_party_code_vendored"] is not False:
            raise IntakeError("this prototype must not vendor third-party source")
    for entry in entries:
        if not entry["search_query"] or not entry["adoption_idea"]:
            raise IntakeError("each project requires a search and an adoption decision")
        if not set(entry["public_reference_ids"]) <= ids:
            raise IntakeError("unresolved public reference")
        if entry["listing_reuse_status"] != "not-cleared":
            raise IntakeError("paid listing assets are not cleared by this registry")
    return {"projects_reviewed": len(entries), "public_sources_pinned": len(sources),
            "marketplace_code_imported": False, "external_execution_enabled": False}


def isolation_report(root: Path, baseline: dict[str, Any]) -> dict[str, Any]:
    """Compare tracked and untracked local paths without changing Git state."""
    base, prefix = baseline["base_commit"], baseline["allowed_new_prefix"]
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise IntakeError("baseline commit is not pinned")
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.PIPE)
    changed = git("diff", "--name-only", "-z", base, "--").split(b"\0")
    new = git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
    paths = sorted({p.decode("utf-8") for p in changed + new if p})
    outside = [p for p in paths if not p.startswith(prefix)]
    return {"base_commit": base, "allowed_prefix": prefix, "changed_paths": paths,
            "outside_prefix": outside, "isolated": not outside,
            "scope": "Local tracked and untracked nonignored paths; remote main checked separately."}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    intake = commands.add_parser("inspect-json", help="Read an Inspect v2 JSON log offline")
    intake.add_argument("path", type=Path)
    intake.add_argument("--expected-sha256", required=True)
    commands.add_parser("catalogue-check", help="Validate the research catalogue and source pins")
    isolation = commands.add_parser("isolation-check", help="Check local changes against the fixed baseline")
    isolation.add_argument("--repo-root", type=Path, default=HERE.parents[1])
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect-json":
            result = inspect_observations(read_bytes(args.path), args.expected_sha256)
        elif args.command == "catalogue-check":
            result = check_catalogue()
        else:
            result = isolation_report(args.repo_root, read_json(read_bytes(HERE / "baseline.json")))
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0 if result.get("isolated", True) else 1
    except (IntakeError, OSError, subprocess.CalledProcessError, KeyError, TypeError) as exc:
        # Do not echo malformed source text or complete exception payloads.
        print(json.dumps({"error": str(exc) if isinstance(exc, IntakeError) else type(exc).__name__}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

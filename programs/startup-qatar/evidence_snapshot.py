"""Read-only, no-model audit of the public evidence used in the Qatar proposal.

This checks recorded artifacts and arithmetic, not the truth of provider telemetry,
security of the historical runner, or correctness of every possible verifier case.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
# Reference of this reviewed evidence baseline. Update deliberately with a new review.
BASE_COMMIT = "794602108eba47c806543c01b7f8d2b7ba9345cc"
RAR = Path("programs/repository-agent-reliability")
EXPERIMENT = "phase-12-cross-model-replication-v1"
OUTPUT = Path(__file__).with_name("evidence-snapshot.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def canonical_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_snapshot(root: Path = ROOT) -> dict:
    root = root.resolve()
    input_hashes = {}

    def read_bytes(relative: Path) -> bytes:
        path = root / relative
        require(path.resolve().is_relative_to(root), f"Outside repository: {relative}")
        raw = path.read_bytes()
        input_hashes[relative.as_posix()] = hashlib.sha256(raw).hexdigest()
        return raw

    def read(relative: Path) -> dict:
        return json.loads(read_bytes(relative))

    attempts = []
    hashed_records = 0
    for directory in sorted((root / RAR / "tasks").glob("AP-*/evidence/live/*")):
        if not directory.is_dir():
            continue
        relative = directory.relative_to(root)
        record = read(relative / "evaluation.json")
        manifest = read(relative / "manifest.json")
        for key in ("task_id", "run_label", "source_commit", "final_verdict"):
            require(record[key] == manifest[key], f"{relative}: {key} mismatch")
        require(record["task_id"] == directory.parents[2].name,
                f"{relative}: task directory mismatch")
        verdict = record["final_verdict"]
        require(verdict in ("VERIFIED_PASS", "VERIFIED_FAIL", "HOLD"),
                f"{relative}: unknown verdict")
        nested = record.get("evaluation")
        scored = nested or (record if record.get("runtime_schema") == "agent-workspace-v1" else None)
        if scored:
            stored_hash = scored["record_hash"]
            content = {k: v for k, v in scored.items() if k != "record_hash"}
            require(canonical_hash(content) == stored_hash, f"{relative}: record hash mismatch")
            require(stored_hash == manifest["evaluation_record_hash"],
                    f"{relative}: manifest record hash mismatch")
            require(scored["final_verdict"] == verdict, f"{relative}: scored verdict mismatch")
            hashed_records += 1
        else:
            require(verdict == "HOLD", f"{relative}: scored evidence missing")
        # Preserve the published metrics' explicit nested-claim population.
        # The workspace/IDE schema has no explicit stored agent-success boolean.
        metric_record = nested or {}
        claimed = metric_record.get("agent_claimed_success")
        public_passed = metric_record.get("public_validation", {}).get("passed")
        if claimed is not None:
            require(type(claimed) is bool, f"{relative}: invalid success claim")
        if public_passed is not None:
            require(type(public_passed) is bool, f"{relative}: invalid public-test result")
        false_green = claimed is True and public_passed is True and verdict == "VERIFIED_FAIL"
        if metric_record.get("false_green") is not None:
            require(metric_record["false_green"] is false_green,
                    f"{relative}: false-green flag contradicts recorded outcomes")
        provider = record.get("provider") or {}
        kind = record.get("attempt_kind", "initial")
        require(kind in ("initial", "repair"), f"{relative}: unknown attempt kind")
        attempts.append({
            "run_label": record["run_label"], "task_id": record["task_id"],
            "kind": kind, "verdict": verdict,
            "provider": provider.get("name", manifest.get("provider")),
            "model": provider.get("model", manifest.get("model")),
            "explicit_success": claimed, "public_tests_passed": public_passed,
            "false_green": false_green,
            "candidate_admitted": (record.get("candidate_admission") or {}).get("accepted", manifest.get("candidate_admitted")),
            "parent_hash": (record.get("parent") or {}).get("record_hash") or manifest.get("parent_record_hash"),
            "repair_conversion": record.get("repair_conversion", manifest.get("repair_conversion")),
            "path": relative.as_posix(),
        })
    labels = [a["run_label"] for a in attempts]
    require(len(labels) == len(set(labels)), "Duplicate run labels would double-count evidence")
    require(bool(attempts), "No attempts discovered")
    verdicts = Counter(a["verdict"] for a in attempts)
    kinds = Counter(a["kind"] for a in attempts)
    claims = [a for a in attempts if a["explicit_success"] is True]
    green_population = [a for a in claims if a["public_tests_passed"] is True]
    false_greens = [a for a in green_population if a["false_green"]]
    initial_population = [a for a in green_population if a["kind"] == "initial"]
    episodes = defaultdict(list)
    for attempt in attempts:
        if attempt["kind"] == "repair":
            require(bool(attempt["parent_hash"]), "Repair parent hash missing")
            episodes[attempt["parent_hash"]].append(attempt)
    converted = sum(any(a["verdict"] == "VERIFIED_PASS" and a["repair_conversion"] is True
                        for a in episode) for episode in episodes.values())
    counts = {
        "attempts_total": len(attempts), "initial_attempts": kinds["initial"],
        "repair_attempts": kinds["repair"], "verified_pass": verdicts["VERIFIED_PASS"],
        "verified_fail": verdicts["VERIFIED_FAIL"], "hold": verdicts["HOLD"],
        "candidate_admitted": sum(a["candidate_admitted"] is True for a in attempts),
        "explicit_claim_coverage": sum(a["explicit_success"] is not None for a in attempts),
        "public_test_observations": sum(a["public_tests_passed"] is not None for a in attempts),
        "false_green_count": len(false_greens), "repair_episodes": len(episodes),
        "repair_episodes_converted": converted,
    }
    published = read(RAR / "metrics/summary.json")
    require(counts == published["counts"], "Raw attempt counts disagree with published summary")
    rates = {
        "false_green_rate": (len(false_greens), len(green_population)),
        "initial_false_green_rate": (sum(a["false_green"] for a in initial_population), len(initial_population)),
        "claim_evidence_gap": (sum(a["verdict"] != "VERIFIED_PASS" for a in claims), len(claims)),
        "repair_conversion": (converted, len(episodes)),
    }
    for name, (numerator, denominator) in rates.items():
        require((published["metrics"][name]["numerator"], published["metrics"][name]["denominator"])
                == (numerator, denominator), f"Published {name} arithmetic mismatch")
    qualification = []
    for path in sorted((root / RAR / "tasks").glob("AP-*/evidence/verifier-qualification.json")):
        record = read(path.relative_to(root))
        controls = record["controls"]
        mutations = [c for c in controls if c["name"].startswith("mutation_")]
        rejected = sum(c["actual"] == "FAIL" for c in mutations)
        require(len(mutations) == record["critical_mutations_total"] and
                rejected == record["critical_mutations_rejected"], f"{path}: mutation summary mismatch")
        require(len({c["name"] for c in controls}) == len(controls), f"{path}: duplicate controls")
        reference = [c for c in controls if c["name"] == "reference"]
        bad = [c for c in controls if c["name"] == "known_bad"]
        require(len(reference) == len(bad) == 1, f"{path}: required controls missing")
        require(record["reference_passed"] == (reference[0]["actual"] == "PASS") and
                record["known_bad_rejected"] == (bad[0]["actual"] == "FAIL"), f"{path}: control mismatch")
        if record["status"] == "QUALIFIED":
            require(record["reference_passed"] is True and record["known_bad_rejected"] is True
                    and rejected == len(mutations), f"{path}: qualification contradicts controls")
        qualification.append({"task_id": record["task_id"], "status": record["status"],
                              "mutations": len(mutations), "rejected": rejected})
    require({a["task_id"] for a in attempts} == {q["task_id"] for q in qualification},
            "Attempt tasks and qualification tasks disagree")
    qualified = sum(q["status"] == "QUALIFIED" for q in qualification)
    mutations = sum(q["mutations"] for q in qualification)
    rejected = sum(q["rejected"] for q in qualification)
    require((qualified, mutations, rejected) ==
            (published["verifier_qualification"]["qualified_tasks"],
             published["verifier_qualification"]["critical_mutations_total"],
             published["verifier_qualification"]["critical_mutations_rejected"]),
            "Published qualification counts disagree")
    result = RAR / "experiments/results" / EXPERIMENT
    promotion = read(result / "promotion.json")
    plan = read(RAR / "experiments" / f"{EXPERIMENT}.json")
    require(canonical_hash(plan) == promotion["experiment_plan_sha256"], "Phase 12 plan hash mismatch")
    for name, expected in promotion["batch_artifact_sha256"].items():
        require(hashlib.sha256(read_bytes(result / name)).hexdigest() == expected,
                f"Phase 12 batch artifact hash mismatch: {name}")
    by_label = {a["run_label"]: a for a in attempts}
    batch = []
    configurations = Counter()
    for item in promotion["attempts"]:
        directory = RAR / item["canonical_evidence_dir"]
        require(item["run_label"] in by_label, "Phase 12 attempt missing from aggregate")
        attempt = by_label[item["run_label"]]
        require(attempt["path"] == directory.as_posix(), "Phase 12 path mismatch")
        require(attempt["task_id"] == "AP-001" and attempt["kind"] == "initial",
                "Phase 12 scope changed")
        for name, expected in item["artifact_sha256"].items():
            require(hashlib.sha256(read_bytes(directory / name)).hexdigest() == expected,
                    f"Phase 12 artifact hash mismatch: {directory / name}")
        replay = read(directory / "replay.json")
        require(replay["status"] == "SOURCE_EXACT_REPLAY_VERIFIED" and
                replay["stored_record_hash"] == replay["replayed_record_hash"] == item["evaluation_record_hash"] and
                replay["replayed_verdict"] == attempt["verdict"] and
                replay["replay_provider"] == "mock" and all(v is True for v in replay["checks"].values()),
                f"{directory}: stored replay inconsistency")
        batch.append(attempt)
        configurations[item["configuration_id"]] += 1
    require(len({a["run_label"] for a in batch}) == len(batch), "Duplicate Phase 12 trials")
    return {
        "schema_version": "1.0.0", "reference_commit": BASE_COMMIT,
        "scope": "Read-only audit of stored public artifacts; no new inference or candidate execution",
        "counts": counts, "qualified_tasks": qualified,
        "critical_mutations": {"total": mutations, "rejected": rejected, "escaped": mutations - rejected},
        "metrics": {k: {"numerator": n, "denominator": d} for k, (n, d) in rates.items()},
        "record_hashes_verified": hashed_records,
        "provider_and_model_present": sum(bool(a["provider"] and a["model"]) for a in attempts),
        "missing_provider_or_model": [a["run_label"] for a in attempts if not a["provider"] or not a["model"]],
        "phase12_subset": {"attempts": len(batch), "included_in_total": True,
                           "configurations": dict(sorted(configurations.items())),
                           "verdicts": dict(sorted(Counter(a["verdict"] for a in batch).items())),
                           "false_greens": sum(a["false_green"] for a in batch),
                           "stored_source_exact_replays_verified": len(batch)},
        "false_green_attempts": [{k: a[k] for k in ("task_id", "run_label", "kind", "path")} for a in false_greens],
        "source_inputs": {"files": len(input_hashes), "manifest_sha256": canonical_hash(input_hashes),
                          "sha256_by_path": dict(sorted(input_hashes.items()))},
        "limits": ["No new model run, replay execution, customer pilot or independent security audit is performed by this command.",
                   "Hash consistency does not establish external authenticity or exhaustive verifier correctness.",
                   "The 30 repeated runs cover one task and are already included in 52; no global model ranking is supported.",
                   "IDE metadata is incomplete; the published aggregate excludes its top-level public-test result from the legacy nested-claim population.",
                   "Cost telemetry is incomplete; local zero provider charges exclude labor, hardware and energy."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--write", action="store_true", help="Regenerate the reviewed proposal snapshot")
    action.add_argument("--check", action="store_true", help="Compare with the committed snapshot (default)")
    args = parser.parse_args()
    try:
        snapshot = build_snapshot()
        if args.write:
            OUTPUT.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            require(json.loads(OUTPUT.read_text(encoding="utf-8")) == snapshot,
                    "Evidence snapshot is stale; review changes before --write")
    except (KeyError, OSError, TypeError, ValueError) as error:
        print(f"EVIDENCE AUDIT FAILED: {error}", file=sys.stderr)
        return 1
    print(f"EVIDENCE AUDIT PASS: {snapshot['counts']['attempts_total']} attempts, "
          f"{snapshot['record_hashes_verified']} record hashes, "
          f"{snapshot['source_inputs']['files']} input files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

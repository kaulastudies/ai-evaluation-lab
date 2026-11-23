"""Check freeze-packet metadata offline; never authenticate evidence or authorize execution.

The existing run-plan checker remains the source of the six-decision/15s rules.
Hashes below bind document bytes, NOT the model's context wire serialization.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from research.eo001_coordination.assess_report import unique_object
from research.eo001_coordination.check_run_manifest import check as check_plan

LIMIT = 2_000_000
RESOURCE_KEYS = ("memory_max_bytes", "memory_swap_max_bytes", "pids_max", "cpu_quota_usec", "cpu_period_usec")
TOP_KEYS = {"schema", "contract_sha256", "run_plan_sha256", "source_revisions", "resources",
            "startup_timeout_seconds", "cleanup_timeout_seconds", "timing_boundary",
            "effective_generation_parameters", "evidence_sha256", "containment_observation", "approvals"}
EVIDENCE_KEYS = {"transport_abort", "group_escape_negative_control", "live_scope_stop"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    if not isinstance(data, bytes) or len(data) > LIMIT:
        raise ValueError("invalid bounded input")
    return json.loads(data.decode("utf-8"), object_pairs_hook=unique_object,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def read_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("regular file required")
    with path.open("rb") as stream:
        data = stream.read(LIMIT + 1)
    if len(data) > LIMIT:
        raise ValueError("input too large")
    return data


def digest(value, length=64):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{%d}" % length, value) is not None and value != "0" * length


def integer(value, minimum=1):
    return type(value) is int and value >= minimum


def object_or_empty(value):
    return value if isinstance(value, dict) else {}


def configuration_digest(packet):
    """Approval records are excluded to avoid a circular approval digest."""
    core = {k: v for k, v in packet.items() if k != "approvals"}
    return sha256(json.dumps(core, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def check(packet, plan_bytes, contract_bytes):
    if not isinstance(packet, dict) or packet.get("schema") != "EO001-FREEZE-PACKET/0.2.0":
        raise ValueError("unsupported freeze packet")
    plan = decode(plan_bytes)
    plan_result = check_plan(plan)
    problems = ["run_plan." + p for p in plan_result["unresolved_or_invalid_fields"]]

    def require(condition, name):
        if not condition:
            problems.append(name)

    require(set(packet) == TOP_KEYS, "packet.fields")
    require(isinstance(contract_bytes, bytes) and 0 < len(contract_bytes) <= LIMIT, "contract.bytes")
    require(packet.get("contract_sha256") == sha256(contract_bytes), "contract_sha256")
    require(packet.get("run_plan_sha256") == sha256(plan_bytes), "run_plan_sha256")
    pins = object_or_empty(packet.get("source_revisions"))
    require(set(pins) == {"lab_reviewer", "forge_integrated", "containment_collector"}, "source_revisions.fields")
    for key in ("lab_reviewer", "forge_integrated", "containment_collector"):
        require(digest(pins.get(key), 40), "source_revisions." + key)
    require(pins.get("forge_integrated") == plan.get("forge_adapter_commit"), "source_revisions.plan_match")
    require(pins.get("lab_reviewer") == plan.get("lab_adapter_commit"), "source_revisions.lab_match")
    require(pins.get("containment_collector") == pins.get("forge_integrated"), "source_revisions.integrated_collector")
    resources = object_or_empty(packet.get("resources"))
    require(set(resources) == set(RESOURCE_KEYS), "resources.fields")
    for key in RESOURCE_KEYS:
        require(integer(resources.get(key), 0 if key == "memory_swap_max_bytes" else 1), "resources." + key)
    for key in ("startup_timeout_seconds", "cleanup_timeout_seconds"):
        require(integer(packet.get(key)), key)
    require(packet.get("timing_boundary") == "complete_warmed_decision", "timing_boundary")
    effective = packet.get("effective_generation_parameters")
    require(isinstance(effective, dict) and bool(effective), "effective_generation_parameters")
    require(effective == plan.get("generation_parameters"), "effective_generation_parameters.plan_match")
    evidence = object_or_empty(packet.get("evidence_sha256"))
    require(set(evidence) == EVIDENCE_KEYS, "evidence_sha256.fields")
    for key in sorted(EVIDENCE_KEYS):
        require(digest(evidence.get(key)), "evidence_sha256." + key)
    valid_hashes = [v for v in evidence.values() if digest(v)]
    require(len(set(valid_hashes)) == 3, "evidence_sha256.distinct_controls")
    obs = object_or_empty(packet.get("containment_observation"))
    require(bool(obs), "containment_observation")
    require(obs.get("method") == "supervisor_procfs_and_cgroup_v2", "containment.method")
    require(obs.get("worker_self_report_only") is False, "containment.external_observer")
    require(obs.get("source_commit") == pins.get("containment_collector") and digest(obs.get("source_commit"), 40), "containment.source_commit")
    require(digest(obs.get("artifact_sha256")) and obs.get("artifact_sha256") == evidence.get("live_scope_stop"), "containment.artifact_sha256")
    before, after = obs.get("scope_identity_before_sha256"), obs.get("scope_identity_after_sha256")
    require(digest(before) and before == after, "containment.scope_identity")
    observed = object_or_empty(obs.get("observed_limits"))
    require(set(observed) == set(RESOURCE_KEYS) and observed == resources and all(
        integer(observed.get(k), 0 if k == "memory_swap_max_bytes" else 1) for k in RESOURCE_KEYS), "containment.resource_readback")
    require(obs.get("detached_descendant_live_before_stop") is True, "containment.live_detached_descendant")
    identity = object_or_empty(obs.get("identity_before"))
    repeated = object_or_empty(obs.get("identity_before_signal"))
    fields = {"pid", "starttime_ticks", "pgrp", "session"}
    require(set(identity) == fields and set(repeated) == fields and identity == repeated and
            all(integer(identity.get(k), 2 if k in ("pid", "pgrp", "session") else 1) for k in fields), "containment.pid_identity")
    require(type(obs.get("subtree_populated_after")) is int and obs["subtree_populated_after"] == 0,
            "containment.subtree_empty")
    require(obs.get("remaining_descendant_pids") == [] and type(obs.get("remaining_descendant_pids")) is list,
            "containment.remaining_descendants")
    require(obs.get("post_stop_observation_available") is True, "containment.post_stop_observation")
    elapsed, budget = obs.get("cleanup_elapsed_ms"), packet.get("cleanup_timeout_seconds")
    require(integer(elapsed, 0) and integer(budget) and elapsed <= budget * 1000, "containment.cleanup_deadline")
    require(obs.get("provenance") == "UNVERIFIED_EXTERNAL", "containment.provenance")
    approvals = packet.get("approvals")
    if not isinstance(approvals, list):
        approvals = []
    require(len(approvals) == 2, "approvals.two_reviews")
    roles, references = [], []
    core_digest = configuration_digest(packet)
    for item in approvals:
        if not isinstance(item, dict):
            problems.append("approvals.invalid_record")
            continue
        roles.append(item.get("role"))
        ref = item.get("reference")
        references.append(ref if isinstance(ref, str) else "")
        require(item.get("decision") == "approve", "approvals.decision")
        require(isinstance(ref, str) and re.fullmatch(
            r"https://github\.com/(kaulastudies/ai-evaluation-lab|jgaethle10/forge-operator)/(issues|pull)/[0-9]+#issuecomment-[0-9]+", ref) is not None,
            "approvals.reference")
        require(item.get("configuration_sha256") == core_digest, "approvals.configuration_sha256")
    require(len(roles) == 2 and all(isinstance(r, str) for r in roles) and sorted(roles) == ["evercraft", "lab"], "approvals.roles")
    require(len(references) == 2 and len(set(references)) == 2, "approvals.distinct_reviews")
    return {
        "schema": "EO001-FREEZE-CHECK/0.2.0",
        "state": "NEEDS_REVIEW" if problems else "FIELDS_COMPLETE_REVIEW_REQUIRED",
        "unresolved_or_invalid_fields": sorted(set(problems)),
        "configuration_sha256": core_digest,
        "contract_sha256": sha256(contract_bytes),
        "run_plan_sha256": sha256(plan_bytes),
        "execution_authorized": False,
        "field_evidence_authenticated": False,
        "review_identity_or_authority_verified": False,
        "referenced_artifact_bytes_verified": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = check(decode(read_bytes(args.packet)), read_bytes(args.plan), read_bytes(args.contract))
    except (ValueError, TypeError, OSError, UnicodeError, RecursionError):
        print("INVALID_FREEZE_PACKET")
        return 2
    print(json.dumps(result, indent=2))
    return 2 if result["unresolved_or_invalid_fields"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

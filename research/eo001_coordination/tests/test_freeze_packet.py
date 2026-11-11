"""Synthetic metadata controls only; no host collection, model run, or approval proof."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from research.eo001_coordination.check_freeze_packet import (
    check, configuration_digest, decode, main, read_bytes, sha256,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = b"Synthetic contract for deterministic unit tests.\n"


def encoded(obj):
    return (json.dumps(obj, indent=2, allow_nan=False) + "\n").encode()


def fixtures():
    plan = json.loads((ROOT / "run_plan.proposed.json").read_text())
    for key in ("lab_adapter_commit", "forge_adapter_commit"):
        plan[key] = "a" * 40 if key.startswith("lab") else "b" * 40
    for key in ("model_sha256", "runtime_sha256", "prompt_sha256", "context_serialization_sha256", "warmup_prompt_sha256"):
        plan[key] = "c" * 64
    for key in ("context_serialization", "host_configuration", "output_naming", "cleanup_checks"):
        plan[key] = "synthetic-fixture-only"
    plan.update(generation_parameters={"temperature": 0, "seed": "unsupported"},
                review_references={"lab": "fixture-lab", "evercraft": "fixture-forge"},
                max_output_tokens=128, warmup_timeout_seconds=30)
    resources = {"memory_max_bytes": 8000000000, "memory_swap_max_bytes": 0,
                 "pids_max": 64, "cpu_quota_usec": 150000, "cpu_period_usec": 100000}
    packet = {
        "schema": "EO001-FREEZE-PACKET/0.2.0", "contract_sha256": sha256(CONTRACT),
        "run_plan_sha256": sha256(encoded(plan)),
        "source_revisions": {"lab_reviewer": "a" * 40, "forge_integrated": "b" * 40,
                             "containment_collector": "b" * 40},
        "resources": resources, "startup_timeout_seconds": 60, "cleanup_timeout_seconds": 5,
        "timing_boundary": "complete_warmed_decision",
        "effective_generation_parameters": copy.deepcopy(plan["generation_parameters"]),
        "evidence_sha256": {"transport_abort": "d" * 64, "group_escape_negative_control": "e" * 64,
                            "live_scope_stop": "f" * 64},
        "containment_observation": {
            "method": "supervisor_procfs_and_cgroup_v2", "worker_self_report_only": False,
            "source_commit": "b" * 40, "artifact_sha256": "f" * 64,
            "scope_identity_before_sha256": "1" * 64, "scope_identity_after_sha256": "1" * 64,
            "observed_limits": copy.deepcopy(resources), "detached_descendant_live_before_stop": True,
            "identity_before": {"pid": 202, "starttime_ticks": 900, "pgrp": 202, "session": 202},
            "identity_before_signal": {"pid": 202, "starttime_ticks": 900, "pgrp": 202, "session": 202},
            "subtree_populated_after": 0, "remaining_descendant_pids": [],
            "post_stop_observation_available": True, "cleanup_elapsed_ms": 900,
            "provenance": "UNVERIFIED_EXTERNAL",
        },
        "approvals": [],
    }
    approve_fixture(packet)
    return packet, plan


def approve_fixture(packet):
    """Fabricated records test structure only; the checker MUST NOT trust identities."""
    packet["approvals"] = [
        {"role": role, "decision": "approve", "configuration_sha256": configuration_digest(packet),
         "reference": "https://github.com/" + repo + "/issues/35#issuecomment-" + number}
        for role, repo, number in (("lab", "kaulastudies/ai-evaluation-lab", "1"),
                                  ("evercraft", "jgaethle10/forge-operator", "2"))
    ]


class FreezePacketTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.plan = fixtures()

    def result(self):
        return check(self.packet, encoded(self.plan), CONTRACT)

    def blocked(self, reason):
        result = self.result()
        self.assertEqual(result["state"], "NEEDS_REVIEW")
        self.assertIn(reason, result["unresolved_or_invalid_fields"])
        self.assertFalse(result["execution_authorized"])

    def test_complete_fixture_never_authenticates_or_authorizes(self):
        result = self.result()
        self.assertEqual(result["state"], "FIELDS_COMPLETE_REVIEW_REQUIRED")
        for key in ("execution_authorized", "field_evidence_authenticated",
                    "review_identity_or_authority_verified", "referenced_artifact_bytes_verified"):
            self.assertIs(result[key], False)

    def test_checked_in_proposal_remains_held(self):
        packet = decode((ROOT / "freeze_packet.proposed.json").read_bytes())
        result = check(packet, (ROOT / "run_plan.proposed.json").read_bytes(),
                       (ROOT / "EXPERIMENT_CONTRACT_v0.2.md").read_bytes())
        self.assertEqual(result["state"], "NEEDS_REVIEW")
        self.assertNotIn("contract_sha256", result["unresolved_or_invalid_fields"])
        self.assertNotIn("run_plan_sha256", result["unresolved_or_invalid_fields"])
        self.assertFalse(result["execution_authorized"])

    def test_contract_byte_drift_blocks(self):
        result = check(self.packet, encoded(self.plan), CONTRACT + b" ")
        self.assertIn("contract_sha256", result["unresolved_or_invalid_fields"])

    def test_plan_whitespace_change_also_changes_binding(self):
        result = check(self.packet, encoded(self.plan) + b"\n", CONTRACT)
        self.assertIn("run_plan_sha256", result["unresolved_or_invalid_fields"])

    def test_source_drift_invalidates_approvals(self):
        self.packet["source_revisions"]["forge_integrated"] = "c" * 40
        self.blocked("approvals.configuration_sha256")

    def test_changed_resource_settings_invalidate_approvals(self):
        self.packet["resources"]["pids_max"] = 65
        self.blocked("approvals.configuration_sha256")

    def test_no_approval_records_block(self):
        self.packet["approvals"] = []
        self.blocked("approvals.two_reviews")

    def test_two_lab_records_are_not_two_party_review(self):
        self.packet["approvals"][1]["role"] = "lab"
        self.blocked("approvals.roles")

    def test_reused_review_reference_blocks(self):
        self.packet["approvals"][1]["reference"] = self.packet["approvals"][0]["reference"]
        self.blocked("approvals.distinct_reviews")

    def test_bare_link_without_review_comment_blocks(self):
        self.packet["approvals"][0]["reference"] = "https://github.com/kaulastudies/ai-evaluation-lab/pull/51"
        self.blocked("approvals.reference")

    def test_request_changes_is_not_approval(self):
        self.packet["approvals"][0]["decision"] = "request_changes"
        self.blocked("approvals.decision")

    def test_mixed_forge_branches_block(self):
        self.packet["source_revisions"]["containment_collector"] = "c" * 40
        self.blocked("source_revisions.integrated_collector")

    def test_nonhex_and_zero_commits_block(self):
        for value in ("s" * 40, "0" * 40, "main", True):
            with self.subTest(value=value):
                self.packet["source_revisions"]["forge_integrated"] = value
                self.blocked("source_revisions.forge_integrated")

    def test_worker_echo_is_not_supervisor_readback(self):
        self.packet["containment_observation"]["worker_self_report_only"] = True
        self.blocked("containment.external_observer")

    def test_observed_limits_must_match_requested_limits(self):
        self.packet["containment_observation"]["observed_limits"]["pids_max"] = 12
        self.blocked("containment.resource_readback")

    def test_boolean_limit_is_not_numeric_limit(self):
        self.packet["resources"]["memory_swap_max_bytes"] = False
        self.blocked("resources.memory_swap_max_bytes")

    def test_unbounded_or_missing_limits_block(self):
        for value in (None, "max", -1, 0):
            self.packet["resources"]["memory_max_bytes"] = value
            self.blocked("resources.memory_max_bytes")

    def test_group_stop_without_live_detached_child_blocks(self):
        self.packet["containment_observation"]["detached_descendant_live_before_stop"] = False
        self.blocked("containment.live_detached_descendant")

    def test_same_pid_with_changed_starttime_is_rejected(self):
        self.packet["containment_observation"]["identity_before_signal"]["starttime_ticks"] += 1
        self.blocked("containment.pid_identity")

    def test_missing_identity_starttime_blocks(self):
        del self.packet["containment_observation"]["identity_before"]["starttime_ticks"]
        self.blocked("containment.pid_identity")

    def test_recreated_scope_identity_blocks(self):
        self.packet["containment_observation"]["scope_identity_after_sha256"] = "2" * 64
        self.blocked("containment.scope_identity")

    def test_nonempty_subtree_blocks(self):
        self.packet["containment_observation"]["subtree_populated_after"] = 1
        self.blocked("containment.subtree_empty")

    def test_false_does_not_masquerade_as_populated_zero(self):
        self.packet["containment_observation"]["subtree_populated_after"] = False
        self.blocked("containment.subtree_empty")

    def test_remaining_descendant_blocks_even_with_claimed_empty_subtree(self):
        self.packet["containment_observation"]["remaining_descendant_pids"] = [202]
        self.blocked("containment.remaining_descendants")

    def test_missing_after_observation_is_not_cleanup_success(self):
        self.packet["containment_observation"]["post_stop_observation_available"] = False
        self.blocked("containment.post_stop_observation")

    def test_cleanup_overrun_blocks(self):
        self.packet["containment_observation"]["cleanup_elapsed_ms"] = 5001
        self.blocked("containment.cleanup_deadline")

    def test_public_provenance_cannot_be_promoted(self):
        self.packet["containment_observation"]["provenance"] = "HARDWARE_VERIFIED"
        self.blocked("containment.provenance")

    def test_one_receipt_cannot_stand_for_three_distinct_controls(self):
        self.packet["evidence_sha256"]["transport_abort"] = "f" * 64
        self.blocked("evidence_sha256.distinct_controls")

    def test_effective_generation_settings_mismatch_blocks(self):
        self.packet["effective_generation_parameters"]["temperature"] = 0.9
        self.blocked("effective_generation_parameters.plan_match")

    def test_legacy_timeout_and_step_limits_still_apply(self):
        for key, value in (("decision_timeout_seconds", 60), ("max_decisions_per_case", 12), ("replace_failed_attempts", True)):
            packet, plan = fixtures()
            plan[key] = value
            packet["run_plan_sha256"] = sha256(encoded(plan))
            approve_fixture(packet)
            result = check(packet, encoded(plan), CONTRACT)
            self.assertEqual(result["state"], "NEEDS_REVIEW")
            self.assertTrue(any(x.startswith("run_plan.") for x in result["unresolved_or_invalid_fields"]))

    def test_duplicate_json_and_nan_block(self):
        for payload in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.assertRaises(ValueError):
                decode(payload)

    def test_symlink_input_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source.json"
            source.write_bytes(encoded(self.packet))
            link = Path(temp) / "link.json"
            link.symlink_to(source)
            with self.assertRaises(ValueError):
                read_bytes(link)

    def test_cli_is_read_only_and_complete_metadata_is_not_authorization(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name, data in (("packet", encoded(self.packet)), ("plan", encoded(self.plan)), ("contract", CONTRACT)):
                (root / name).write_bytes(data)
            before = {p.name: p.read_bytes() for p in root.iterdir()}
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(["--packet", str(root / "packet"), "--plan", str(root / "plan"), "--contract", str(root / "contract")])
            self.assertEqual(code, 0)
            self.assertFalse(json.loads(output.getvalue())["execution_authorized"])
            self.assertEqual(before, {p.name: p.read_bytes() for p in root.iterdir()})

    def test_cli_missing_file_returns_two_without_echoing_path(self):
        output = io.StringIO()
        with redirect_stdout(output):
            code = main(["--packet", "/missing/private-name", "--plan", "/missing/plan", "--contract", "/missing/contract"])
        self.assertEqual(code, 2)
        self.assertEqual(output.getvalue().strip(), "INVALID_FREEZE_PACKET")


if __name__ == "__main__":
    unittest.main()

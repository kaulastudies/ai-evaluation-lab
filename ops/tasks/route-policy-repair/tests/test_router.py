import copy
import importlib.util
import os
import pathlib
import unittest

ROUTER = pathlib.Path(os.environ.get("ROUTER_PATH", "/app/router.py"))
spec = importlib.util.spec_from_file_location("submitted_router", ROUTER)
router = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(router)

def task(**updates):
    base = {
        "id": "x",
        "privacy": "public",
        "complexity": "low",
        "task_type": "summarization",
        "local_confidence": 0.9,
        "local_available": True,
        "cloud_available": True,
    }
    base.update(updates)
    return base

class RoutePolicyTests(unittest.TestCase):
    def decision(self, item):
        result = router.route_batch([item])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["position"], 0)
        self.assertEqual(result[0]["id"], item["id"])
        self.assertEqual(result[0]["policy_version"], "R1")
        return result[0]

    def test_sensitive_never_cloud(self):
        for privacy in ("confidential", "restricted"):
            d = self.decision(task(privacy=privacy, local_confidence=0.9))
            self.assertEqual((d["route"], d["reason_code"]), ("local", "SENSITIVE_LOCAL"))

            d = self.decision(task(privacy=privacy, local_available=False, cloud_available=True))
            self.assertEqual((d["route"], d["reason_code"]), ("blocked", "SENSITIVE_BLOCKED"))

            d = self.decision(task(privacy=privacy, local_confidence=0.64, cloud_available=True))
            self.assertEqual((d["route"], d["reason_code"]), ("blocked", "SENSITIVE_BLOCKED"))

    def test_deterministic_never_cloud_fallback(self):
        for kind in ("arithmetic", "regex", "schema_validation"):
            d = self.decision(task(task_type=kind, local_available=True, local_confidence=0.1))
            self.assertEqual((d["route"], d["reason_code"]), ("local", "DETERMINISTIC_LOCAL"))

            d = self.decision(task(task_type=kind, local_available=False, cloud_available=True))
            self.assertEqual((d["route"], d["reason_code"]), ("blocked", "DETERMINISTIC_BLOCKED"))

    def test_public_routing(self):
        d = self.decision(task(local_confidence=0.80))
        self.assertEqual((d["route"], d["reason_code"]), ("local", "PUBLIC_LOCAL_CONFIDENT"))

        d = self.decision(task(local_confidence=0.79, cloud_available=True))
        self.assertEqual((d["route"], d["reason_code"]), ("cloud", "PUBLIC_CLOUD_ESCALATION"))

        d = self.decision(task(local_confidence=0.4, cloud_available=False, local_available=True))
        self.assertEqual((d["route"], d["reason_code"]), ("local", "PUBLIC_LOCAL_FALLBACK"))

        d = self.decision(task(local_available=False, cloud_available=False))
        self.assertEqual((d["route"], d["reason_code"]), ("blocked", "NO_PROVIDER"))

    def test_duplicate_ids_preserve_position_and_order(self):
        items = [
            task(id="dup", local_confidence=0.95),
            task(id="dup", local_confidence=0.1),
            task(id="z", privacy="restricted", local_confidence=0.9),
        ]
        result = router.route_batch(items)
        self.assertEqual([r["id"] for r in result], ["dup", "dup", "z"])
        self.assertEqual([r["position"] for r in result], [0, 1, 2])

    def test_input_not_mutated_and_result_is_deterministic(self):
        items = [task(id="a"), task(id="b", privacy="confidential")]
        before = copy.deepcopy(items)
        one = router.route_batch(items)
        two = router.route_batch(items)
        self.assertEqual(items, before)
        self.assertEqual(one, two)

    def test_result_schema(self):
        decision = self.decision(task())
        self.assertEqual(
            set(decision),
            {"id", "position", "route", "reason_code", "policy_version"},
        )

if __name__ == "__main__":
    unittest.main()

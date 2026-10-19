import math
import unittest
from research.futureproof_eval.qproof_audit import audit, analyze

class QProofTests(unittest.TestCase):
    def test_known_good(self):
        report = audit({"cases": [{"id": "zero", "theta_radians": 0, "shots": 100, "ones": 0}, {"id": "half", "theta_radians": math.pi/2, "shots": 100, "ones": 50}]})
        self.assertEqual(report["flagged"], 0)
    def test_biased_counts(self):
        self.assertEqual(analyze({"id": "bad", "theta_radians": math.pi, "shots": 100, "ones": 0})["flag"], "REVIEW")
    def test_repeatable(self):
        data = {"cases": [{"id": "demo", "theta_radians": 0, "shots": 100, "ones": 0}]}
        self.assertEqual(audit(data)["evidence_sha256"], audit(data)["evidence_sha256"])
    def test_invalid(self):
        with self.assertRaises(ValueError):
            audit({"cases": [{"id": "x", "shots": 0, "ones": 0, "theta_radians": 0}]})
        with self.assertRaises(ValueError):
            audit({"cases": [{"id": "x", "shots": 10, "ones": 0, "theta_radians": 0}, {"id": "x", "shots": 10, "ones": 0, "theta_radians": 0}]})

if __name__ == "__main__":
    unittest.main()

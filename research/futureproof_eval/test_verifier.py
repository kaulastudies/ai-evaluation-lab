"""Offline acceptance and negative controls for reference verifier."""
import math
import unittest
from research.futureproof_eval.verifier import evaluate, born_probability

class VerifierTests(unittest.TestCase):
    def test_born_rule(self):
        self.assertAlmostEqual(born_probability(0), 0)
        self.assertAlmostEqual(born_probability(math.pi / 2), .5)
        self.assertAlmostEqual(born_probability(math.pi), 1)
    def test_repeatable_evidence(self):
        a = evaluate("half", math.pi / 2, 50, 100)
        b = evaluate("half", math.pi / 2, 50, 100)
        self.assertTrue(a.passed)
        self.assertEqual(a.evidence_sha256, b.evidence_sha256)
        self.assertNotEqual(a.evidence_sha256, evaluate("half", math.pi / 2, 51, 100).evidence_sha256)
    def test_known_bad(self):
        self.assertFalse(evaluate("bad", math.pi, 0, 100).passed)
    def test_invalid_counts(self):
        for ones, shots in [(11, 10), (-1, 10), (0, 0)]:
            with self.subTest(ones=ones, shots=shots):
                with self.assertRaises(ValueError):
                    evaluate("invalid", 0, ones, shots)
        with self.assertRaises(TypeError):
            evaluate("bool", 0, True, 100)
    def test_nonfinite(self):
        with self.assertRaises(ValueError):
            born_probability(float("nan"))

if __name__ == "__main__":
    unittest.main()

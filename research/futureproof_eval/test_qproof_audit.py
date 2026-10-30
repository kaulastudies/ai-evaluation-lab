import math
import unittest
from research.futureproof_eval.qproof_audit import audit, analyze, load_payload

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

    def test_invalid_angles_and_boolean_counts(self):
        for angle in (True, False, float('nan'), float('inf'), 10**400, '0'):
            with self.subTest(angle=repr(angle)), self.assertRaises(ValueError):
                analyze({"id": "x", "shots": 100, "ones": 0, "theta_radians": angle})
        for field in ('shots', 'ones'):
            case = {"id": "x", "shots": 100, "ones": 0, "theta_radians": 0}
            case[field] = True
            with self.subTest(field=field), self.assertRaises(ValueError):
                analyze(case)

    def test_closed_schema_and_invalid_ids(self):
        good = {"id": "x", "shots": 100, "ones": 0, "theta_radians": 0}
        invalid = [None, [], {"cases": [good], "accepted": True},
                   {"cases": [dict(good, accepted=True)]}]
        invalid += [{"cases": [dict(good, id=name)]} for name in ([], {}, None, True, '')]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                audit(payload)

    def test_ambiguous_json_rejected(self):
        for raw in ('{"cases":[],"cases":[]}', '{"cases":[{"shots":1,"shots":2}]}',
                    '{"cases":NaN}', '{"cases":Infinity}', '{"cases":-Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                load_payload(raw)

    def test_input_tampering_changes_hash(self):
        case = {"id": "x", "shots": 100, "ones": 0, "theta_radians": 0}
        before = audit({"cases": [case]})
        case['ones'] = 1
        self.assertNotEqual(before['evidence_sha256'], audit({"cases": [case]})['evidence_sha256'])

if __name__ == "__main__":
    unittest.main()

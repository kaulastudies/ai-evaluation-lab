import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("portfolio", ROOT / "portfolio.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PortfolioTests(unittest.TestCase):
    def setUp(self):
        self.declaration = json.loads((ROOT / "demo-declaration.json").read_text())
        self.packet = p.packet(self.declaration, list(p.RUNS))

    def test_roundtrip_retains_false_green_and_success(self):
        p.verify(json.loads(json.dumps(self.packet)))
        self.assertEqual([s["verdict"] for s in self.packet["samples"]],
                         ["VERIFIED_FAIL", "VERIFIED_PASS"])
        self.assertTrue(self.packet["samples"][0]["false_green"])

    def test_recomputed_hash_cannot_hide_invented_verdict(self):
        forged = copy.deepcopy(self.packet)
        forged["samples"][0]["verdict"] = "VERIFIED_PASS"
        forged["packet_sha256"] = p.digest(p.canonical({k: v for k, v in forged.items() if k != "packet_sha256"}))
        with self.assertRaises(ValueError):
            p.verify(forged)

    def test_repair_cannot_omit_failed_parent(self):
        only_repair = p.packet(self.declaration, [p.RUNS[1]])
        self.assertEqual([s["run"] for s in only_repair["samples"]], list(p.RUNS))
        only_repair["samples"].pop(0)
        with self.assertRaises(ValueError):
            p.verify(only_repair)

    def test_export_requires_affirmative_consent(self):
        self.declaration["sharing_consent"] = False
        with self.assertRaises(ValueError):
            p.packet(self.declaration, list(p.RUNS))

    def test_ai_disclosure_cannot_be_empty(self):
        self.declaration["ai_assistance"] = " "
        with self.assertRaises(ValueError):
            p.packet(self.declaration, list(p.RUNS))

    def test_untrusted_html_is_text(self):
        self.declaration["alias"] = "<script>alert(1)</script>"
        page = p.render(p.packet(self.declaration, list(p.RUNS)))
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)

    def test_only_curated_public_evidence_is_read(self):
        with self.assertRaises(ValueError):
            p.sample("../../private")

    def test_packet_cannot_claim_identity_verification(self):
        forged = copy.deepcopy(self.packet)
        forged["declaration_status"] = "IDENTITY_VERIFIED"
        with self.assertRaises(ValueError):
            p.verify(forged)

    def test_private_extra_declaration_fields_are_rejected(self):
        self.declaration["phone"] = "not needed"
        with self.assertRaises(ValueError):
            p.packet(self.declaration, list(p.RUNS))


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from eval_lab.alpha_demo import run


class AlphaDemoTests(unittest.TestCase):
    def test_regression_becomes_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            records = run(Path(tmp))
            regressions = [r for r in records if r["run_label"] == "regression"]
            self.assertEqual(len(regressions), 1)
            self.assertEqual(regressions[0]["final_status"], "ACCEPTED")
            self.assertIsNotNone(regressions[0]["regression_of"])

            summary = json.loads((Path(tmp) / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["records"], 6)
            self.assertEqual(summary["accepted"], 2)
            self.assertEqual(summary["needs_edit"], 1)
            self.assertEqual(summary["rejected"], 3)
            self.assertEqual(summary["disagreements"], 1)
            self.assertEqual(summary["regressions"], 1)


if __name__ == "__main__":
    unittest.main()
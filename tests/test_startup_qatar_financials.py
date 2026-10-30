"""Regressions for planning defects found during the separate QA review."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest


PROGRAM = Path(__file__).resolve().parents[1] / "programs" / "startup-qatar"
SPEC = importlib.util.spec_from_file_location("qatar_financial_model", PROGRAM / "financial_model.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


class PlanningInputTests(unittest.TestCase):
    def setUp(self):
        self.assumptions = json.loads((PROGRAM / "financial-assumptions.json").read_text())

    def test_nonfinite_rates_and_cash_never_produce_a_financial_report(self):
        for section, key in (("unit_economics", "labor_economic_hourly_rate"),
                             ("costs", "founder_draw_monthly"),
                             ("funding", "contingency_percent")):
            for invalid in (float("nan"), float("inf"), -float("inf"), True):
                with self.subTest(section=section, key=key, invalid=invalid):
                    data = copy.deepcopy(self.assumptions)
                    data[section][key] = invalid
                    with self.assertRaises(ValueError):
                        MODEL.build(data)

    def test_hiring_capacity_cannot_precede_its_cost_or_use_an_invalid_month(self):
        for section, key in (("monthly_capacity", "funded_engineer_start_month"),
                             ("costs", "local_engineer_start_month")):
            for invalid in (0, 13, 1.5, True):
                with self.subTest(section=section, key=key, invalid=invalid):
                    data = copy.deepcopy(self.assumptions)
                    data[section][key] = invalid
                    with self.assertRaises(ValueError):
                        MODEL.build(data)
        data = copy.deepcopy(self.assumptions)
        data["monthly_capacity"]["funded_engineer_start_month"] = 6
        data["costs"]["local_engineer_start_month"] = 7
        with self.assertRaisesRegex(ValueError, "same month"):
            MODEL.build(data)


if __name__ == "__main__":
    unittest.main()

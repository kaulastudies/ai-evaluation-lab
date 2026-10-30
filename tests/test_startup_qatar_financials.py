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

    def test_unpriced_follow_on_cannot_masquerade_as_cash_receipts(self):
        report = MODEL.build(self.assumptions)
        base = report["scenarios"]["base_hypothesis"]
        self.assertEqual(sum(m["initial_request_if_approved_and_received"] for m in base["months"]), 12000)
        self.assertEqual(base["months"][2]["illustrative_cash_with_initial_request_only"], 1800)
        self.assertEqual(base["totals"]["first_unfunded_month_if_spending_continues"], 4)
        self.assertEqual(base["totals"]["illustrative_ending_cash_initial_request_only"], -21550)
        self.assertEqual(base["totals"]["ending_cash_full_ceiling_sensitivity_only"], 66450)
        self.assertIsNone(report["historical_actuals"]["cash_balance"])
        bad = copy.deepcopy(self.assumptions)
        bad["funding"]["follow_on_reviews"][0]["amount"] = 30000
        with self.assertRaisesRegex(ValueError, "cannot be counted as funding"):
            MODEL.build(bad)

    def test_initial_request_must_be_recosted_when_validation_costs_change(self):
        data = copy.deepcopy(self.assumptions)
        data["costs"]["founder_draw_monthly"] = 3000
        with self.assertRaisesRegex(ValueError, "request is stale"):
            MODEL.build(data)
        data["funding"]["current_initial_request"] = 16000
        report = MODEL.build(data)
        self.assertEqual(report["funding_sizing"]["initial_stage_cash_cost"], 13200)
        self.assertEqual(report["funding_sizing"]["initial_stage_contingency_not_spent"], 1980)


if __name__ == "__main__":
    unittest.main()

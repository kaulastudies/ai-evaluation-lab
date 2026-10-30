"""Reproduce an illustrative planning model. No bank/API access or actual accounts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def validate(data: dict) -> None:
    """Reject incomplete periods and nonsensical numeric planning assumptions."""
    def nonnegative(value, name):
        if (isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) or value < 0):
            raise ValueError(f"{name} must be a finite nonnegative number")

    for section in ("unit_economics", "monthly_capacity"):
        for key, value in data[section].items():
            nonnegative(value, f"{section}.{key}")
    for key, value in data["costs"].items():
        if key.endswith("_by_month"):
            if len(value) != 12:
                raise ValueError(f"{key} needs exactly 12 months")
            for amount in value:
                nonnegative(amount, key)
        else:
            nonnegative(value, key)
        if key.endswith("_start_month") and (type(value) is not int or not 1 <= value <= 12):
            raise ValueError(f"{key} must be an integer in 1..12")
    for name, scenario in data["scenarios"].items():
        for key in ("pilots_completed_by_month", "active_recurring_customers_by_month"):
            if len(scenario[key]) != 12:
                raise ValueError(f"{name}.{key} needs exactly 12 months")
            if any(type(n) is not int or n < 0 for n in scenario[key]):
                raise ValueError(f"{name}.{key} needs nonnegative integer counts")
        lag = scenario["collection_lag_months"]
        if type(lag) is not int or not 0 <= lag <= 12:
            raise ValueError("collection lag must be an integer from 0 through 12")
    funding = data["funding"]
    nonnegative(funding["contingency_percent"], "contingency_percent")
    if type(funding["rounding_increment"]) is not int or funding["rounding_increment"] <= 0:
        raise ValueError("rounding_increment must be a positive integer")
    nonnegative(funding["current_initial_request"], "current_initial_request")
    for key in ("initial_request_month", "initial_stage_months"):
        if type(funding[key]) is not int or not 1 <= funding[key] <= 12:
            raise ValueError(f"{key} must be an integer in 1..12")
    if funding["initial_request_month"] != 1:
        raise ValueError("this relative-start plan requires initial funding before month 1 spending")
    if (type(funding["initial_request_rounding_increment"]) is not int
            or funding["initial_request_rounding_increment"] <= 0):
        raise ValueError("initial_request_rounding_increment must be a positive integer")
    seen_review_months = set()
    for review in funding["follow_on_reviews"]:
        month = review["month"]
        if type(month) is not int or not funding["initial_stage_months"] < month <= 12:
            raise ValueError("follow-on review must occur after the initial stage and within year 1")
        if month in seen_review_months:
            raise ValueError("duplicate follow-on review month")
        seen_review_months.add(month)
        if review["amount"] is not None:
            raise ValueError("unpriced follow-on reviews cannot be counted as funding")
    cap = data["monthly_capacity"]
    start = cap["funded_engineer_start_month"]
    if type(start) is not int or not 1 <= start <= 12:
        raise ValueError("funded_engineer_start_month must be an integer in 1..12")
    if start != data["costs"]["local_engineer_start_month"]:
        raise ValueError("engineer delivery capacity and salary must begin in the same month")
    if cap["founder_non_delivery_hours"] > cap["founder_total_hours"]:
        raise ValueError("founder non-delivery hours exceed total hours")


def build(data: dict) -> dict:
    validate(data)
    u, c, cap = (data[k] for k in ("unit_economics", "costs", "monthly_capacity"))
    pilot_direct = (u["pilot_delivery_hours"] * u["labor_economic_hourly_rate"]
                    + u["pilot_external_review_cash"] + u["pilot_compute_cash"])
    recurring_direct = (u["recurring_delivery_hours"] * u["labor_economic_hourly_rate"]
                        + u["recurring_compute_cash"])
    scenarios = {}
    for name, scenario in data["scenarios"].items():
        invoices = [p * u["pilot_price"] + r * u["recurring_monthly_price"]
                    for p, r in zip(scenario["pilots_completed_by_month"],
                                    scenario["active_recurring_customers_by_month"])]
        lag = scenario["collection_lag_months"]
        # Zero here is a modelling origin, not an assertion of the founder's bank balance.
        unfinanced_balance = initial_only_balance = 0
        months = []
        for index in range(12):
            month = index + 1
            pilots = scenario["pilots_completed_by_month"][index]
            recurring = scenario["active_recurring_customers_by_month"][index]
            fixed = c["founder_draw_monthly"] + c["infrastructure_monthly"]
            for prefix in ("qatar_workspace_admin", "qatar_business_development", "local_engineer"):
                if month >= c[f"{prefix}_start_month"]:
                    amount_key = "local_engineer_all_in_monthly" if prefix == "local_engineer" else f"{prefix}_monthly"
                    fixed += c[amount_key]
            one_off = (c["setup_legal_travel_by_month"][index]
                       + c["independent_security_review_by_month"][index])
            direct = (pilots * (u["pilot_external_review_cash"] + u["pilot_compute_cash"])
                      + recurring * u["recurring_compute_cash"])
            outflow = fixed + one_off + direct
            receipts = invoices[index - lag] if index >= lag else 0
            initial_funding = (data["funding"]["current_initial_request"]
                               if month == data["funding"]["initial_request_month"] else 0)
            unfinanced_balance += receipts - outflow
            initial_only_balance += receipts + initial_funding - outflow
            demand_hours = pilots * u["pilot_delivery_hours"] + recurring * u["recurring_delivery_hours"]
            available = cap["founder_total_hours"] - cap["founder_non_delivery_hours"]
            if month >= cap["funded_engineer_start_month"]:
                available += cap["funded_engineer_total_hours"]
            months.append({
                "month": month, "pilots_completed": pilots, "active_recurring_customers": recurring,
                "invoiced_revenue": invoices[index], "cash_collected": receipts,
                "fixed_cash_cost": fixed, "one_off_cash_cost": one_off,
                "external_delivery_cash_cost": direct, "total_cash_cost": outflow,
                "delivery_hours_required": demand_hours, "delivery_hours_available": available,
                "capacity_exceeded": demand_hours > available,
                "initial_request_if_approved_and_received": initial_funding,
                "cumulative_unfinanced_cash_delta": unfinanced_balance,
                "illustrative_cash_with_initial_request_only": initial_only_balance,
                "additional_funding_required_before_continuing": initial_only_balance < 0,
            })
        total = lambda key: sum(m[key] for m in months)
        scenarios[name] = {
            "description": scenario["description"], "months": months,
            "totals": {
                "pilots_completed": total("pilots_completed"),
                "recurring_customer_months": total("active_recurring_customers"),
                "invoiced_revenue": sum(invoices), "cash_collected": total("cash_collected"),
                "year_end_receivables": sum(invoices) - total("cash_collected"),
                "cash_cost": total("total_cash_cost"),
                "unfinanced_cash_delta": unfinanced_balance,
                "peak_unfinanced_cash_requirement": max(0, -min(m["cumulative_unfinanced_cash_delta"] for m in months)),
                "illustrative_ending_cash_initial_request_only": initial_only_balance,
                "first_unfunded_month_if_spending_continues": next((m["month"] for m in months if m["additional_funding_required_before_continuing"]), None),
                "capacity_exceeded_months": [m["month"] for m in months if m["capacity_exceeded"]],
            },
        }
    worst_cost = max(s["totals"]["cash_cost"] for s in scenarios.values())
    reserve = round(worst_cost * data["funding"]["contingency_percent"] / 100, 2)
    increment = data["funding"]["rounding_increment"]
    ceiling = int(-(-(worst_cost + reserve) // increment) * increment)
    stage_months = data["funding"]["initial_stage_months"]
    initial_cost = max(sum(m["total_cash_cost"] for m in scenario["months"][:stage_months])
                       for scenario in scenarios.values())
    initial_reserve = round(initial_cost * data["funding"]["contingency_percent"] / 100, 2)
    initial_increment = data["funding"]["initial_request_rounding_increment"]
    derived_initial_request = int(-(-(initial_cost + initial_reserve) // initial_increment) * initial_increment)
    if data["funding"]["current_initial_request"] != derived_initial_request:
        raise ValueError("current initial request is stale relative to stage costs and reserve; re-cost the request")
    for scenario in scenarios.values():
        scenario["totals"]["ending_cash_full_ceiling_sensitivity_only"] = ceiling + scenario["totals"]["unfinanced_cash_delta"]
    return {
        "schema_version": "1.1", "as_of": data["as_of"], "currency": data["currency"],
        "status": data["status"],
        "assumptions_sha256": hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
        "historical_actuals": data["historical_actuals"],
        "unit_economics": {
            "pilot_direct_economic_cost": pilot_direct,
            "pilot_contribution_before_overhead_tax": u["pilot_price"] - pilot_direct,
            "pilot_contribution_percent": round((u["pilot_price"] - pilot_direct) / u["pilot_price"] * 100, 2) if u["pilot_price"] else None,
            "recurring_direct_economic_cost": recurring_direct,
            "recurring_contribution_before_overhead_tax": u["recurring_monthly_price"] - recurring_direct,
            "recurring_contribution_percent": round((u["recurring_monthly_price"] - recurring_direct) / u["recurring_monthly_price"] * 100, 2) if u["recurring_monthly_price"] else None,
            "note": "Labor is valued at replacement cost here; cash model pays monthly founder draw and funded engineer, not a second hourly labor payment.",
        },
        "funding_sizing": {
            "current_initial_request": data["funding"]["current_initial_request"],
            "initial_stage_months": stage_months,
            "initial_stage_cash_cost": initial_cost,
            "initial_stage_contingency_not_spent": initial_reserve,
            "initial_request_rounding_headroom": derived_initial_request - initial_cost - initial_reserve,
            "initial_request_gate": data["funding"]["initial_request_gate"],
            "follow_on_reviews": data["funding"]["follow_on_reviews"],
            "no_collection_stress_cash_cost": worst_cost, "contingency_reserve_not_spent": reserve,
            "rounded_indicative_ceiling": ceiling,
            "note": "The only current proposed request is the initial validation amount. It is not approved or received. Follow-on amounts remain unknown and do not enter cash receipts. Monthly initial-only cash shows the shortfall if the full operating plan continues without new funding; stop or re-scope before that happens. The full-ceiling ending-cash sensitivity is separate and is not a financing schedule or upfront ask.",
        },
        "scenarios": scenarios, "unpriced_exclusions": data["unpriced_exclusions"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assumptions", type=Path, default=HERE / "financial-assumptions.json")
    parser.add_argument("--output", type=Path, default=HERE / "financials.json")
    parser.add_argument("--check", action="store_true", help="Fail if committed output differs from assumptions")
    args = parser.parse_args()
    def reject_constant(value):
        raise ValueError(f"non-finite JSON number is not allowed: {value}")

    result = build(json.loads(args.assumptions.read_text(encoding="utf-8"), parse_constant=reject_constant))
    rendered = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if args.check:
        if not args.output.exists() or args.output.read_text(encoding="utf-8") != rendered:
            raise SystemExit("financial output is stale; regenerate and review")
        print("Financial assumptions, arithmetic and committed output agree (planning model only).")
    else:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()

from datetime import date
from decimal import Decimal

import pytest

from services.financial_engine import (
    calculate_financial_health, estimate_monthly_expenses, simulate_debts, asset_allocation,
    EngineProfile, EngineAsset, EngineLiability, EngineGoal,
)

TODAY = date(2026, 1, 15)


def profile(salary=100000, rent=20000, savings=600000):
    return EngineProfile(salary=salary, rent=rent, current_savings=savings)


def loan(name, balance, rate, emi):
    return EngineLiability(name=name, type="Loan", outstanding_amount=balance, interest_rate=rate, monthly_payment=emi)


def goal(name, amount, when="2027-01-15", priority="Medium", saved=0):
    return EngineGoal(name=name, target_amount=amount, target_date=when, priority=priority, saved_amount=saved)


def exp(amount, d):
    return {"amount": amount, "date": d}


def run(**kw):
    args = dict(profile=profile(), expenses=[], assets=[], liabilities=[], goals=[], today=TODAY)
    args.update(kw)
    return calculate_financial_health(**args)


# ---------- basics ----------

def test_basic_surplus_and_burn():
    h = run(expenses=[exp(10000, "2026-01-05"), exp(5000.50, "2026-01-10")])
    # 15,000.50 spent in 15 of 31 days -> projected 31,001.03 for the month
    assert h["month_to_date_spent"] == 15000.50
    assert h["monthly_expenses"] == 31001.03
    assert h["monthly_burn"] == 51001.03
    assert h["surplus"] == 48998.97


def test_only_liquid_assets_count_for_emergency():
    illiquid = EngineAsset(name="House", type="Real Estate", value=1_000_000, liquidity_score=1)
    liquid = EngineAsset(name="FD", type="Bank", value=50000, liquidity_score=5)
    h = run(profile=profile(rent=25000, savings=50000), assets=[illiquid, liquid])
    assert h["emergency_months"] == 4.0
    assert h["net_worth"] == 1_100_000


def test_no_burn_no_division_error():
    h = run(profile=profile(rent=0))
    assert h["emergency_months"] == 600000.0


def test_deterministic():
    assert run() == run()


# ---------- 1. surplus is split once ----------

def test_goals_share_one_surplus_by_priority():
    # ₹30k surplus, three goals each needing ~₹25.8k/mo -> only the High one is funded
    goals = [goal("Low", 300000, priority="Low"), goal("High", 300000, priority="High"),
             goal("Medium", 300000, priority="Medium")]
    h = run(profile=profile(salary=70000, rent=40000), goals=goals)
    assert h["surplus"] == 30000
    status = {g["name"]: g["status"] for g in h["analyzed_goals"]}
    assert status == {"High": "On Track", "Medium": "Unrealistic", "Low": "Unrealistic"}
    alloc = {g["name"]: g["allocated_monthly"] for g in h["analyzed_goals"]}
    assert alloc["Low"] == 0
    assert alloc["High"] + alloc["Medium"] == 30000
    assert h["recommended_investment"] == 0


def test_plan_never_exceeds_surplus():
    h = run(liabilities=[loan("Card", 50000, 36, 2000)], goals=[goal("Trip", 100000)],
            profile=profile(savings=10000))
    p = h["plan"]
    total = p["emergency_fund"] + p["debt_prepayment"] + p["goals"] + p["investment"]
    assert total == pytest.approx(h["surplus"], abs=0.02)


# ---------- 2. projection ----------

def test_projection_counts_loan_principal_and_labels_years():
    h = run(liabilities=[loan("Car", 400000, 9, 12000)])
    first = h["projections"][0]
    # month 1: 3,000 interest, 12,000 EMI -> 391,000 left
    assert first["debt"] == 391000
    assert first["month"] == "Feb 26"
    assert h["projections"][-1]["month"] == "Jan 27"
    # net worth rises by surplus + principal repaid (+ growth), not surplus alone
    assert first["net_worth"] - h["net_worth"] > h["surplus"]


def test_projection_uses_per_asset_returns():
    crypto = EngineAsset(name="BTC", type="Crypto", value=100000, liquidity_score=4)
    stock = EngineAsset(name="NIFTY", type="Stock", value=100000, liquidity_score=4)
    base = dict(profile=profile(salary=20000, rent=20000, savings=0))
    a = run(assets=[crypto], **base)["projections"][-1]["net_worth"]
    b = run(assets=[stock], **base)["projections"][-1]["net_worth"]
    assert a == 100000          # crypto assumed flat
    assert b == pytest.approx(111000, abs=1)  # 11% for stocks


def test_deficit_drains_savings_in_projection():
    h = run(profile=profile(salary=20000, rent=30000, savings=100000))
    assert h["projections"][-1]["net_worth"] < 100000
    assert h["projections"][0]["net_worth_real"] <= h["projections"][0]["net_worth"]


# ---------- 3. avalanche ----------

def test_avalanche_pays_highest_rate_first_and_saves_interest():
    loans = [loan("Car", 400000, 9, 12000), loan("Card", 100000, 36, 5000)]
    h = run(liabilities=loans)
    ds = h["debt_strategy"]
    order = {l["name"]: l["paid_off_month"] for l in ds["payoff_order"]}
    assert ds["payoff_order"][0]["name"] == "Card"
    assert order["Card"] < order["Car"]
    assert ds["interest_saved"] > 0
    assert ds["recommended_extra_payment"] == 63000  # all spare money until the 36% card is gone


def test_freed_emi_rolls_to_next_loan():
    a, b = loan("A", 10000, 20, 10000), loan("B", 100000, 10, 1000)
    with_roll = simulate_debts([a, b], rollover=True)
    without = simulate_debts([a, b], rollover=False)
    assert with_roll["months"] < without["months"]


def test_debt_trap_detected():
    h = run(profile=profile(salary=30000, rent=29000), liabilities=[loan("Card", 10_000_000, 40, 1000)])
    assert h["debt_strategy"]["months_to_freedom"] == -1
    assert h["debt_strategy"]["freedom_date"] == "Never (Debt Trap)"


def test_goals_funded_after_high_interest_debt_clears():
    # All ₹63k goes to the card for ~2 months; the trip is judged on the 10 months left after that.
    h = run(liabilities=[loan("Card", 100000, 36, 5000)], goals=[goal("Trip", 120000, when="2026-12-15")])
    g = h["analyzed_goals"][0]
    assert h["plan"]["goals"] == 0
    assert g["funding_starts_in_months"] == 2
    assert g["status"] == "On Track"
    assert g["required_monthly"] > 120000 / 11  # compressed into fewer months


# ---------- 4. goals ----------

def test_goal_uses_inflation_and_sip():
    g = goal("House", 2_000_000, when="2036-01-15", priority="High")
    out = run(profile=profile(salary=500000), goals=[g])["analyzed_goals"][0]
    assert out["inflation_adjusted_target"] == pytest.approx(3_581_695, abs=1)  # 20L * 1.06^10
    # Much less than the naive 35.8L / 120 = ~29.8k thanks to 10% returns
    assert 15000 < out["required_monthly"] < 20000


def test_saved_amount_reduces_requirement():
    fresh = run(goals=[goal("Car", 600000)])["analyzed_goals"][0]["required_monthly"]
    half = run(goals=[goal("Car", 600000, saved=300000)])["analyzed_goals"][0]["required_monthly"]
    assert half < fresh / 2 + 1000


def test_overdue_and_achieved_goals():
    h = run(goals=[goal("Old", 50000, when="2025-06-01"), goal("Done", 50000, saved=60000)])
    status = {g["name"]: g["status"] for g in h["analyzed_goals"]}
    assert status == {"Old": "Overdue", "Done": "Achieved"}


# ---------- 5. expense estimate ----------

def test_early_month_uses_trailing_average():
    history = [exp(30000, f"2025-{m:02d}-10") for m in (10, 11, 12)]
    est = estimate_monthly_expenses(history + [exp(3000, "2026-01-02")], date(2026, 1, 3))
    assert est["monthly_estimate"] == Decimal("30000.00")
    assert est["method"] == "trailing_average"


def test_new_user_without_history_uses_current_month():
    est = estimate_monthly_expenses([exp(3000, "2026-01-02")], date(2026, 1, 3))
    assert est["monthly_estimate"] == Decimal("3000.00")  # too early to extrapolate


def test_heavy_current_month_beats_history():
    history = [exp(10000, "2025-12-10")]
    est = estimate_monthly_expenses(history + [exp(20000, "2026-01-05")], date(2026, 1, 10))
    assert est["monthly_estimate"] == Decimal("62000.00")  # 20k * 31 / 10


# ---------- 6. investment safety ----------

def test_no_investing_without_emergency_fund():
    h = run(profile=profile(savings=0))
    assert h["recommended_investment"] == 0
    assert h["plan"]["emergency_fund"] == h["surplus"]
    assert "emergency" in h["investment_note"].lower()


def test_no_investing_with_high_interest_debt():
    h = run(liabilities=[loan("Card", 500000, 36, 5000)])
    assert h["recommended_investment"] == 0
    assert "12%" in h["investment_note"]


def test_invests_when_safe():
    h = run(profile=profile(savings=1_000_000))
    assert h["recommended_investment"] == h["surplus"]
    assert h["investment_note"] is None


# ---------- 7. score ----------

def test_score_is_smooth_and_explained():
    just_under = run(profile=profile(salary=100000, rent=50000, savings=5.9 * 50000))
    just_over = run(profile=profile(salary=100000, rent=50000, savings=6.1 * 50000))
    assert abs(just_over["score"] - just_under["score"]) <= 2
    keys = {b["key"] for b in just_under["score_breakdown"]}
    assert {"savings_rate", "emergency_fund", "debt_to_income", "goals"} <= keys


def test_overspending_is_penalised():
    ok = run(profile=profile(salary=50000, rent=50000, savings=0))
    bad = run(profile=profile(salary=50000, rent=60000, savings=0))
    assert bad["score"] < ok["score"]
    assert any(b["key"] == "overspending" for b in bad["score_breakdown"])


def test_high_debt_to_income_lowers_score():
    low = run(liabilities=[loan("Home", 1_000_000, 8, 10000)])
    high = run(liabilities=[loan("Home", 5_000_000, 8, 45000)])
    assert high["score"] < low["score"]


# ---------- 8. allocation ----------

def test_allocation_sums_to_exactly_100():
    assets = [EngineAsset(name=n, type=n, value=1, liquidity_score=4) for n in ("A", "B")]
    alloc = asset_allocation(assets, Decimal(1))
    assert sum(Decimal(str(v)) for v in alloc.values()) == 100

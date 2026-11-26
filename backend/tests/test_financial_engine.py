from datetime import datetime
from decimal import Decimal

from services.financial_engine import (
    calculate_financial_health, EngineProfile, EngineAsset, EngineLiability, EngineGoal, DEBT_TRAP,
)

TODAY = datetime(2026, 1, 15)


def profile(salary=100000, rent=20000, savings=50000):
    return EngineProfile(salary=salary, rent=rent, current_savings=savings)


def run(**kw):
    args = dict(profile=profile(), expenses=[], assets=[], liabilities=[], goals=[], today=TODAY)
    args.update(kw)
    return calculate_financial_health(**args)


def test_basic_surplus_and_burn():
    h = run(expenses=[{"amount": 10000}, {"amount": 5000.50}])
    assert h["monthly_burn"] == 35000.50
    assert h["surplus"] == 64999.50
    assert h["net_worth"] == 50000


def test_only_liquid_assets_count_for_emergency():
    illiquid = EngineAsset(name="House", type="Real Estate", value=1_000_000, liquidity_score=1)
    liquid = EngineAsset(name="FD", type="Cash", value=50000, liquidity_score=5)
    h = run(assets=[illiquid, liquid], expenses=[{"amount": 5000}])
    # liquid = 50k savings + 50k FD over 25k burn
    assert h["emergency_months"] == 4.0
    assert h["net_worth"] == 1_100_000


def test_no_expenses_no_division_error():
    h = run(profile=profile(rent=0), expenses=[])
    assert h["emergency_months"] == 50000.0


def test_debt_paid_off():
    loan = EngineLiability(name="Car", type="Loan", outstanding_amount=100000,
                           interest_rate=10, monthly_payment=10000)
    h = run(liabilities=[loan])
    ds = h["debt_strategy"]
    assert 0 < ds["months_to_freedom"] < 12
    assert ds["freedom_date"] != "Never (Debt Trap)"


def test_debt_trap_detected():
    loan = EngineLiability(name="Card", type="Credit", outstanding_amount=10_000_000,
                           interest_rate=40, monthly_payment=1000)
    h = run(profile=profile(salary=30000, rent=29000), liabilities=[loan])
    assert h["debt_strategy"]["months_to_freedom"] == DEBT_TRAP
    assert h["debt_strategy"]["freedom_date"] == "Never (Debt Trap)"
    assert h["score"] <= 50


def test_goal_status():
    easy = EngineGoal(name="Phone", target_amount=60000, target_date="2027-01-15", priority="Low")
    hard = EngineGoal(name="House", target_amount=50_000_000, target_date="2027-01-15", priority="High")
    h = run(goals=[easy, hard])
    status = {g["name"]: g["status"] for g in h["analyzed_goals"]}
    assert status == {"Phone": "On Track", "House": "Unrealistic"}


def test_recommended_investment_is_capped():
    h = run(profile=profile(salary=1_000_000, rent=0))
    assert h["recommended_investment"] == float(Decimal("200000"))


def test_deterministic():
    assert run() == run()

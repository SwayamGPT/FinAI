"""
FinAI financial engine.

Deterministic, Decimal-based. Same input (including `today`) -> same output.

Pipeline:
  1. Monthly expense estimate (guards against "early in the month" optimism)
  2. Monthly burn, surplus, liquidity
  3. Surplus plan: the surplus is split ONCE, in order:
       emergency fund -> high-interest debt -> goals (by priority) -> investing
  4. Debt payoff: per-loan avalanche simulation, compared with minimum payments
  5. Goals: inflation-adjusted targets, SIP maths, savings so far, funded from the plan
  6. Net-worth projection: per-bucket growth, debt amortisation, plan contributions
  7. Health score: smooth weighted components with an explainable breakdown
"""
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, InvalidOperation
from typing import Optional

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel

ENGINE_VERSION = "4.0.0"

# --- ASSUMPTIONS (annual, nominal) ---
INFLATION = Decimal("0.06")
CASH_RETURN = Decimal("0.035")          # savings account
INVEST_RETURN = Decimal("0.10")         # diversified equity mutual fund
GOAL_RETURN_SHORT = Decimal("0.06")     # goals < 3 years: debt funds / FDs
GOAL_RETURN_LONG = Decimal("0.10")      # goals >= 3 years: equity
GOAL_LONG_HORIZON_MONTHS = 36
DEFAULT_ASSET_RETURN = Decimal("0.06")
ASSET_RETURNS = {
    "cash": CASH_RETURN, "bank": CASH_RETURN, "savings": CASH_RETURN,
    "fd": Decimal("0.07"), "fixed deposit": Decimal("0.07"),
    "mutual fund": Decimal("0.10"), "stock": Decimal("0.11"), "stocks": Decimal("0.11"),
    "gold": Decimal("0.08"), "real estate": Decimal("0.05"), "property": Decimal("0.05"),
    "pf": Decimal("0.0825"), "epf": Decimal("0.0825"), "ppf": Decimal("0.071"),
    "crypto": Decimal("0"),  # too volatile to assume growth
}

# --- RULES ---
EMERGENCY_MIN_MONTHS = Decimal(3)
EMERGENCY_TARGET_MONTHS = Decimal(6)
EMERGENCY_SHARE_BELOW_MIN = Decimal("0.5")    # share of surplus while < 3 months saved
EMERGENCY_SHARE_BELOW_TARGET = Decimal("0.2")  # share of surplus while 3-6 months saved
HIGH_INTEREST_RATE = Decimal(12)               # % p.a.; such debt is cleared before investing
MIN_DAYS_TO_EXTRAPOLATE = 7
TRAILING_MONTHS = 3
MAX_DEBT_MONTHS = 360
PROJECTION_MONTHS = 12
PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

ZERO = Decimal(0)
CENT = Decimal("0.01")


# --- INTERNAL MODELS ---
class EngineAsset(BaseModel):
    name: str; type: str; value: Decimal; liquidity_score: int


class EngineLiability(BaseModel):
    name: str; type: str; outstanding_amount: Decimal; interest_rate: Decimal; monthly_payment: Decimal


class EngineGoal(BaseModel):
    name: str
    target_amount: Decimal
    target_date: str
    priority: str
    saved_amount: Decimal = ZERO
    id: Optional[str] = None


class EngineProfile(BaseModel):
    salary: Decimal; rent: Decimal; current_savings: Decimal


# --- SAFE MATH UTILS ---
def to_d(value):
    """Safely converts input to Decimal. Returns 0 on failure."""
    try:
        return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


def q(v: Decimal) -> Decimal:
    return v.quantize(CENT, rounding=ROUND_HALF_UP)


def money(v: Decimal) -> float:
    return float(q(v))


def clamp01(v) -> Decimal:
    return max(ZERO, min(Decimal(1), Decimal(v)))


def monthly_rate(annual: Decimal) -> Decimal:
    """Effective monthly rate equivalent to an annual compounded return."""
    return (Decimal(1) + annual) ** (Decimal(1) / Decimal(12)) - Decimal(1)


def asset_return(asset_type: str) -> Decimal:
    return ASSET_RETURNS.get((asset_type or "").strip().lower(), DEFAULT_ASSET_RETURN)


def _parse_date(s) -> Optional[date]:
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# --- 1. EXPENSES ---
def estimate_monthly_expenses(expenses, today: date) -> dict:
    """
    Monthly expense estimate = max(
        this month so far scaled to a full month (only after MIN_DAYS_TO_EXTRAPOLATE days),
        average of the last TRAILING_MONTHS full months that have any logged expenses
    ).
    """
    month_start = today.replace(day=1)
    days_in_month = ((month_start + relativedelta(months=1)) - month_start).days
    days_elapsed = today.day

    month_to_date = ZERO
    by_month = defaultdict(lambda: ZERO)
    for e in expenses:
        d = _parse_date(e.get("date"))
        if d is None:
            continue
        amount = to_d(e.get("amount", 0))
        if d.year == today.year and d.month == today.month:
            month_to_date += amount
        elif d < month_start:
            by_month[(d.year, d.month)] += amount

    if days_elapsed >= MIN_DAYS_TO_EXTRAPOLATE:
        projected_current = month_to_date * Decimal(days_in_month) / Decimal(days_elapsed)
    else:
        projected_current = month_to_date  # too early to extrapolate one or two bills

    previous = []
    for i in range(1, TRAILING_MONTHS + 1):
        m = month_start - relativedelta(months=i)
        if (m.year, m.month) in by_month:
            previous.append(by_month[(m.year, m.month)])
    trailing_average = sum(previous, ZERO) / len(previous) if previous else ZERO

    estimate = max(projected_current, trailing_average)
    return {
        "month_to_date": q(month_to_date),
        "projected_current_month": q(projected_current),
        "trailing_average": q(trailing_average),
        "trailing_months_used": len(previous),
        "monthly_estimate": q(estimate),
        "method": "trailing_average" if trailing_average > projected_current else "current_month",
    }


# --- 4. DEBT SIMULATION ---
def simulate_debts(liabilities, extra: Decimal = ZERO, rollover: bool = True, max_months: int = MAX_DEBT_MONTHS):
    """
    Month-by-month, per-loan simulation.

    rollover=True (avalanche): the payment pool is every loan's EMI plus `extra`. Each active loan gets
    its own EMI first; whatever is left (extra + EMIs freed by paid-off loans) goes to the highest-rate
    loan. `extra` only applies while a high-interest loan is still open.
    rollover=False (baseline): each loan just pays its own EMI.
    """
    loans = sorted(
        [{"name": l.name, "rate": l.interest_rate, "balance": l.outstanding_amount, "emi": l.monthly_payment,
          "mrate": l.interest_rate / Decimal(1200), "paid_off_month": None}
         for l in liabilities if l.outstanding_amount > 0],
        key=lambda x: (-x["rate"], x["balance"]),
    )
    total_emi = sum((l["emi"] for l in loans), ZERO)

    months, total_interest = 0, ZERO
    schedule = []      # debt remaining after each month
    paid_per_month = []
    extra_used = []    # whether `extra` was still being directed to debt that month

    while any(l["balance"] > 0 for l in loans) and months < max_months:
        months += 1
        for l in loans:
            if l["balance"] > 0:
                interest = q(l["balance"] * l["mrate"])
                l["balance"] += interest
                total_interest += interest

        hi_open = any(l["balance"] > 0 and l["rate"] >= HIGH_INTEREST_RATE for l in loans)
        month_extra = extra if hi_open else ZERO
        paid = ZERO
        for l in loans:
            if l["balance"] > 0:
                p = min(l["emi"], l["balance"])
                l["balance"] -= p
                paid += p
        if rollover:
            pool_left = total_emi + month_extra - paid
            for l in loans:  # highest rate first
                if pool_left <= 0:
                    break
                if l["balance"] > 0:
                    p = min(pool_left, l["balance"])
                    l["balance"] -= p
                    paid += p
                    pool_left -= p
        for l in loans:
            if l["balance"] <= 0 and l["paid_off_month"] is None:
                l["balance"] = ZERO
                l["paid_off_month"] = months

        schedule.append(sum((l["balance"] for l in loans), ZERO))
        paid_per_month.append(paid)
        extra_used.append(month_extra > 0)

    cleared = not any(l["balance"] > 0 for l in loans)
    return {
        "cleared": cleared,
        "months": months if cleared else None,
        "total_interest": total_interest,
        "schedule": schedule,
        "paid_per_month": paid_per_month,
        "extra_used": extra_used,
        "total_emi": total_emi,
        "loans": [{"name": l["name"], "interest_rate": float(l["rate"]), "paid_off_month": l["paid_off_month"]}
                  for l in loans],
    }


# --- 5. GOALS ---
def _goal_maths(g: EngineGoal, today: date, delay: int = 0) -> dict:
    """`delay`: months before contributions can start (e.g. while high-interest debt is being cleared)."""
    t_date = _parse_date(g.target_date)
    if t_date is None:
        t_date = today + relativedelta(months=12)
    diff = relativedelta(t_date, today)
    months_left = diff.years * 12 + diff.months
    overdue = t_date < today
    if not overdue and months_left <= 0:
        months_left = 1

    years = Decimal(max(months_left, 0)) / Decimal(12)
    inflated_target = g.target_amount * (Decimal(1) + INFLATION) ** years
    annual_return = GOAL_RETURN_LONG if months_left >= GOAL_LONG_HORIZON_MONTHS else GOAL_RETURN_SHORT
    i = monthly_rate(annual_return)

    if overdue:
        saved_fv = g.saved_amount
        inflated_target = g.target_amount
        remaining = max(ZERO, inflated_target - saved_fv)
        required = ZERO
    else:
        saved_fv = g.saved_amount * (Decimal(1) + i) ** months_left
        remaining = max(ZERO, inflated_target - saved_fv)
        n = months_left - delay
        if remaining <= 0:
            required = ZERO
        elif n <= 0:
            required = remaining  # cannot start in time: effectively needs a lump sum
        else:
            # SIP formula (payment at month end): PMT = FV * i / ((1+i)^n - 1)
            required = remaining * i / ((Decimal(1) + i) ** n - Decimal(1))

    return {
        "months_left": max(months_left, 0),
        "overdue": overdue,
        "inflated_target": inflated_target,
        "expected_return": annual_return,
        "remaining_needed": remaining,
        "required_monthly": required,
        "delay": delay,
    }


# --- 8. ALLOCATION ---
def asset_allocation(assets, current_savings: Decimal) -> dict:
    """Percentages with 1 decimal that always sum to exactly 100 (largest-remainder rounding)."""
    totals = defaultdict(lambda: ZERO)
    for a in assets:
        if a.value > 0:
            totals[a.type] += a.value
    if current_savings > 0:
        totals["Cash"] += current_savings
    grand = sum(totals.values(), ZERO)
    if grand <= 0:
        return {}

    units = {k: v * 1000 / grand for k, v in totals.items()}  # tenths of a percent
    floored = {k: u.to_integral_value(rounding=ROUND_FLOOR) for k, u in units.items()}
    leftover = 1000 - int(sum(floored.values()))
    for k in sorted(units, key=lambda k: (units[k] - floored[k], k), reverse=True)[:leftover]:
        floored[k] += 1
    return {k: float(v / 10) for k, v in floored.items()}


# --- 7. SCORE ---
def _component(key, label, weight, ratio, detail):
    ratio = clamp01(ratio)
    return {"key": key, "label": label, "points": float((ratio * weight).quantize(Decimal("0.1"))),
            "max": weight, "detail": detail}


def health_score(*, salary, surplus, emergency_months, total_emi, hi_debt, debt_trap, goal_statuses, net_worth):
    annual_income = salary * 12
    savings_rate = surplus / salary if salary > 0 else ZERO
    dti = total_emi / salary if salary > 0 else (Decimal(1) if total_emi > 0 else ZERO)

    on_track = sum(1 for s in goal_statuses if s in ("On Track", "Achieved"))
    goal_ratio = Decimal(on_track) / len(goal_statuses) if goal_statuses else Decimal("0.5")

    parts = [
        _component("savings_rate", "Savings rate", 25, savings_rate / Decimal("0.20"),
                   f"Saving {float(savings_rate * 100):.0f}% of income (target 20%)"),
        _component("emergency_fund", "Emergency fund", 25, emergency_months / EMERGENCY_TARGET_MONTHS,
                   f"{float(emergency_months):.1f} months of expenses in liquid savings (target 6)"),
        _component("debt_to_income", "Debt-to-income", 20,
                   ZERO if debt_trap else (Decimal("0.5") - dti) / Decimal("0.3"),
                   "Debt can never be repaid at current payments" if debt_trap
                   else f"EMIs take {float(dti * 100):.0f}% of income (healthy below 20%, risky above 40%)"),
        _component("high_interest_debt", "High-interest debt", 10,
                   Decimal(1) - (hi_debt / (annual_income / 2) if annual_income > 0 else Decimal(hi_debt > 0)),
                   "No debt above 12% interest" if hi_debt <= 0
                   else f"₹{float(q(hi_debt)):,.0f} owed at 12%+ interest"),
        _component("goals", "Goals on track", 10, goal_ratio,
                   f"{on_track} of {len(goal_statuses)} goals funded" if goal_statuses else "No goals set yet"),
        _component("net_worth", "Net worth", 10, net_worth / annual_income if annual_income > 0 else ZERO,
                   "Net worth vs one year of income"),
    ]

    penalty = ZERO
    if surplus < 0 and salary > 0:
        # Overspending: up to -20 points, full penalty at a deficit of 10% of income
        penalty = clamp01((-surplus / salary) / Decimal("0.10")) * 20
        parts.append({"key": "overspending", "label": "Overspending", "points": -float(penalty.quantize(Decimal("0.1"))),
                      "max": 0, "detail": f"Spending ₹{float(q(-surplus)):,.0f} more than you earn each month"})

    total = sum(Decimal(str(p["points"])) for p in parts)
    score = int(max(ZERO, min(Decimal(100), total)).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return score, parts


# --- MAIN ---
def calculate_financial_health(profile, expenses, assets, liabilities, goals, today=None):
    """
    `expenses` should cover the current month and the TRAILING_MONTHS before it (each with `amount`, `date`).
    Goal `saved_amount` is assumed to already sit inside the user's assets/savings, so it is not added to
    net worth again.
    """
    today = today or datetime.now()
    today = today.date() if isinstance(today, datetime) else today

    # 1-2. EXPENSES, BURN, LIQUIDITY
    exp = estimate_monthly_expenses(expenses, today)
    total_debt = sum((l.outstanding_amount for l in liabilities), ZERO)
    total_emi = sum((l.monthly_payment for l in liabilities if l.outstanding_amount > 0), ZERO)
    hi_debt = sum((l.outstanding_amount for l in liabilities if l.interest_rate >= HIGH_INTEREST_RATE), ZERO)

    liquid_assets = profile.current_savings + sum((a.value for a in assets if a.liquidity_score >= 4), ZERO)
    total_assets = profile.current_savings + sum((a.value for a in assets), ZERO)
    net_worth = total_assets - total_debt

    actual_burn = profile.rent + exp["monthly_estimate"] + total_emi
    burn_for_ratio = max(actual_burn, Decimal(1))
    emergency_months = liquid_assets / burn_for_ratio
    surplus = profile.salary - actual_burn

    # 3. SURPLUS PLAN
    remaining = max(ZERO, surplus)
    em_target = EMERGENCY_TARGET_MONTHS * actual_burn
    em_min = EMERGENCY_MIN_MONTHS * actual_burn

    emergency = ZERO
    if remaining > 0 and liquid_assets < em_target:
        share = EMERGENCY_SHARE_BELOW_MIN if liquid_assets < em_min else EMERGENCY_SHARE_BELOW_TARGET
        emergency = min(remaining * share, em_target - liquid_assets)
    remaining -= emergency

    debt_extra = min(remaining, hi_debt) if hi_debt > 0 else ZERO
    sim = simulate_debts(liabilities, extra=debt_extra, rollover=True)

    # While high-interest debt is being prepaid, goals are funded from the same money once that debt is
    # gone: they are judged on the months left after it clears. Otherwise they share what is left now.
    goal_delay = 0
    if debt_extra > 0 and remaining - debt_extra <= 0:
        hi_months = [l["paid_off_month"] for l in sim["loans"] if l["interest_rate"] >= float(HIGH_INTEREST_RATE)]
        if hi_months and all(m is not None for m in hi_months):
            goal_delay = max(hi_months)
    goal_pool = remaining if goal_delay else remaining - debt_extra
    remaining -= debt_extra

    goal_rows = []
    for idx, g in enumerate(goals):
        goal_rows.append((idx, g, _goal_maths(g, today, delay=goal_delay)))
    goal_rows.sort(key=lambda r: (PRIORITY_ORDER.get(r[1].priority, 1), r[2]["months_left"], r[0]))

    analyzed_by_idx = {}
    goals_total = ZERO
    for idx, g, m in goal_rows:
        req = m["required_monthly"]
        if m["remaining_needed"] <= 0:
            status, alloc = "Achieved", ZERO
        elif m["overdue"]:
            status, alloc = "Overdue", ZERO
        elif goal_delay and m["months_left"] <= goal_delay:
            status, alloc = "Unrealistic", ZERO
        else:
            alloc = min(goal_pool, req)
            goal_pool -= alloc
            funded = alloc / req if req > 0 else Decimal(1)
            status = "On Track" if funded >= 1 else ("At Risk" if funded >= Decimal("0.5") else "Unrealistic")
        if not goal_delay:
            goals_total += alloc
            remaining -= alloc
        analyzed_by_idx[idx] = {
            **g.model_dump(),
            "target_amount": money(g.target_amount),
            "saved_amount": money(g.saved_amount),
            "inflation_adjusted_target": money(m["inflated_target"]),
            "expected_return": float(m["expected_return"] * 100),
            "remaining_needed": money(m["remaining_needed"]),
            "required_monthly": money(req),
            "allocated_monthly": money(alloc),
            "shortfall_monthly": money(max(ZERO, req - alloc)),
            "months_left": m["months_left"],
            "funding_starts_in_months": goal_delay,
            "status": status,
        }
    analyzed_goals = [analyzed_by_idx[i] for i in range(len(goals))]

    # Investing is blocked until 3 months of emergency fund exist: leftover tops up the fund first.
    if liquid_assets < em_min and remaining > 0:
        top_up = min(remaining, em_target - liquid_assets - emergency)
        emergency += top_up
        remaining -= top_up
    investment = remaining

    investment_note = None
    if surplus <= 0:
        investment_note = "No surplus to invest: spending exceeds income"
    elif hi_debt > debt_extra:
        investment_note = "Clear debt above 12% interest before investing"
    elif liquid_assets < em_min and investment == 0:
        investment_note = "Build an emergency fund of 3 months' expenses before investing"
    elif investment == 0 and goals_total > 0:
        investment_note = "All spare money is going to your goals"

    plan = {
        "emergency_fund": money(emergency),
        "debt_prepayment": money(debt_extra),
        "goals": money(goals_total),
        "investment": money(investment),
        "order": ["emergency_fund", "debt_prepayment", "goals", "investment"],
    }

    # 4. DEBT STRATEGY
    debt_strategy = {"strategy": "None", "freedom_date": "N/A", "recommended_extra_payment": 0,
                     "months_to_freedom": 0, "interest_saved": 0, "total_interest": 0, "payoff_order": []}
    debt_trap = False
    if total_debt > 0:
        baseline = simulate_debts(liabilities, rollover=False)
        debt_trap = not sim["cleared"]
        interest_saved = (baseline["total_interest"] - sim["total_interest"]) if baseline["cleared"] and sim["cleared"] else None
        debt_strategy = {
            "strategy": "Avalanche",
            "recommended_extra_payment": money(debt_extra),
            "freedom_date": "Never (Debt Trap)" if debt_trap
            else (today + relativedelta(months=sim["months"])).strftime("%b %Y"),
            "months_to_freedom": -1 if debt_trap else sim["months"],
            "total_interest": money(sim["total_interest"]),
            "interest_saved": money(interest_saved) if interest_saved is not None else None,
            "payoff_order": sim["loans"],
        }

    # 6. PROJECTION
    buckets = [[profile.current_savings, monthly_rate(CASH_RETURN), True]]  # [value, monthly rate, liquid]
    for a in assets:
        buckets.append([a.value, monthly_rate(asset_return(a.type)), a.liquidity_score >= 4])
    cash, goal_bucket, invest_bucket = buckets[0], [ZERO, monthly_rate(Decimal("0.08")), False], [ZERO, monthly_rate(INVEST_RETURN), True]
    buckets += [goal_bucket, invest_bucket]

    projections = []
    inflation_m = monthly_rate(INFLATION)
    for month in range(1, PROJECTION_MONTHS + 1):
        for b in buckets:
            b[0] += b[0] * b[1] if b[0] > 0 else ZERO

        paid = sim["paid_per_month"][month - 1] if month <= len(sim["paid_per_month"]) else ZERO
        debt_left = sim["schedule"][month - 1] if month <= len(sim["schedule"]) else ZERO
        available = surplus + total_emi - paid  # money left after actual debt payments

        if available < 0:
            cash[0] += available  # deficit drains savings
        else:
            liquid_now = sum((b[0] for b in buckets if b[2]), ZERO)
            em = min(emergency, max(ZERO, em_target - liquid_now), available)
            g_amt = min(goals_total, available - em)
            cash[0] += em
            goal_bucket[0] += g_amt
            invest_bucket[0] += available - em - g_amt  # investing + freed EMIs/prepayment

        assets_now = sum((b[0] for b in buckets), ZERO)
        nw = assets_now - debt_left
        label_date = today + relativedelta(months=month)
        projections.append({
            "month": label_date.strftime("%b %y"),
            "date": label_date.strftime("%Y-%m"),
            "net_worth": money(nw),
            "net_worth_real": money(nw / (Decimal(1) + inflation_m) ** month),
            "assets": money(assets_now),
            "debt": money(debt_left),
        })

    # 7. SCORE
    score, breakdown = health_score(
        salary=profile.salary, surplus=surplus, emergency_months=emergency_months, total_emi=total_emi,
        hi_debt=hi_debt, debt_trap=debt_trap, goal_statuses=[g["status"] for g in analyzed_goals],
        net_worth=net_worth,
    )

    return {
        "engine_version": ENGINE_VERSION,
        "score": score,
        "score_breakdown": breakdown,
        "net_worth": money(net_worth),
        "surplus": money(surplus),
        "monthly_burn": money(actual_burn),
        "monthly_expenses": money(exp["monthly_estimate"]),
        "month_to_date_spent": money(exp["month_to_date"]),
        "expense_basis": {k: (money(v) if isinstance(v, Decimal) else v) for k, v in exp.items()},
        "total_emi": money(total_emi),
        "recommended_investment": money(investment),
        "investment_note": investment_note,
        "plan": plan,
        "emergency_months": float(emergency_months.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)),
        "emergency_target": money(em_target),
        "debt_strategy": debt_strategy,
        "projections": projections,
        "analyzed_goals": analyzed_goals,
        "allocation": asset_allocation(assets, profile.current_savings),
        "assumptions": {
            "inflation": float(INFLATION * 100),
            "investment_return": float(INVEST_RETURN * 100),
            "cash_return": float(CASH_RETURN * 100),
            "high_interest_threshold": float(HIGH_INTEREST_RATE),
        },
    }

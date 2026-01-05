from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from collections import defaultdict

# --- CONSTANTS ---
HEALTH_WEIGHTS = {
    "savings_rate_good": 10,  # > 20%
    "savings_rate_great": 10, # > 40%
    "debt_low": 10,           # < 30% ratio
    "debt_high_penalty": -15, # > 50% ratio
    "emergency_ok": 10,       # > 3 months
    "emergency_good": 10,     # > 6 months
    "bankruptcy_penalty": -20 # Net worth < 0
}

def to_d(value):
    """Safe Decimal Conversion"""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_financial_health(user_profile, expenses, assets, liabilities, goals):
    # 1. Precision Conversion
    salary = to_d(user_profile.get("salary", 0))
    rent = to_d(user_profile.get("rent", 0))
    current_savings_cash = to_d(user_profile.get("current_savings", 0))
    
    # 2. Aggregations
    total_monthly_expense = sum(to_d(e['amount']) for e in expenses)
    total_debt = sum(to_d(l['outstanding_amount']) for l in liabilities)
    monthly_emi = sum(to_d(l['monthly_payment']) for l in liabilities)
    
    # Liquidity Logic: Only liquidity_score >= 4 counts for emergency fund
    liquid_assets = current_savings_cash + sum(to_d(a['value']) for a in assets if a.get('liquidity_score', 1) >= 4)
    total_assets = current_savings_cash + sum(to_d(a['value']) for a in assets)
    net_worth = total_assets - total_debt

    # 3. Stabilized Burn Rate
    actual_burn = rent + total_monthly_expense + monthly_emi
    baseline_burn = max(actual_burn, salary * Decimal("0.5")) 
    
    emergency_months = (liquid_assets / baseline_burn) if baseline_burn > 0 else Decimal(0)

    # 4. Budget & Surplus
    surplus = salary - actual_burn
    available_to_invest = max(Decimal(0), surplus)
    
    # Advisory Logic: Suggest 30% of surplus, BUT capped at 20% of gross salary
    # This prevents recommending ₹90k investment on ₹3L surplus if lifestyle is lean
    recommended_investment = min(
        available_to_invest * Decimal("0.3"),
        salary * Decimal("0.2") if salary > 0 else Decimal(0)
    )

    # 5. Ratios
    savings_rate = (surplus / salary * 100) if salary > 0 else Decimal(0)
    debt_ratio = (monthly_emi / salary * 100) if salary > 0 else Decimal(0)

    # 6. Goal Feasibility Engine
    analyzed_goals = []
    today = datetime.now()
    
    for g in goals:
        target = to_d(g['target_amount'])
        try:
            t_date = datetime.strptime(g['target_date'], "%Y-%m-%d")
            months_left = (t_date.year - today.year) * 12 + (t_date.month - today.month)
            if months_left <= 0: months_left = 1
        except:
            months_left = 12 
            
        required_monthly = target / Decimal(months_left)
        
        status = "On Track"
        if required_monthly > available_to_invest:
            status = "Impossible" if required_monthly > (available_to_invest * 2) else "At Risk"

        goal_data = {**g}
        goal_data.update({
            "required_monthly": float(required_monthly),
            "months_left": months_left,
            "status": status
        })
        analyzed_goals.append(goal_data)

    # 7. Asset Allocation
    allocation = defaultdict(Decimal)
    if total_assets > 0:
        for a in assets: allocation[a['type']] += to_d(a['value'])
        allocation['Cash'] += current_savings_cash
        allocation = {k: float(round((v / total_assets * 100), 1)) for k, v in allocation.items()}

    # 8. Scoring Engine
    score = 50
    if savings_rate > 20: score += HEALTH_WEIGHTS["savings_rate_good"]
    if savings_rate > 40: score += HEALTH_WEIGHTS["savings_rate_great"]
    if debt_ratio < 30: score += HEALTH_WEIGHTS["debt_low"]
    if debt_ratio > 50: score += HEALTH_WEIGHTS["debt_high_penalty"]
    if emergency_months > 3: score += HEALTH_WEIGHTS["emergency_ok"]
    if emergency_months > 6: score += HEALTH_WEIGHTS["emergency_good"]
    if net_worth < 0: score += HEALTH_WEIGHTS["bankruptcy_penalty"]

    return {
        "score": max(0, min(100, score)),
        "net_worth": float(net_worth),
        "total_assets": float(total_assets),
        "liquid_assets": float(liquid_assets),
        "monthly_burn": float(actual_burn),
        "surplus": float(surplus),
        "recommended_investment": float(recommended_investment),
        "emergency_months": float(round(emergency_months, 1)),
        "savings_rate": float(round(savings_rate, 1)),
        "debt_ratio": float(round(debt_ratio, 1)),
        "monthly_emi_burden": float(monthly_emi),
        "analyzed_goals": analyzed_goals,
        "allocation": allocation
    }
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel
from dateutil.relativedelta import relativedelta
from collections import defaultdict

ENGINE_VERSION = "3.1.0"

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
    # FIX: Added ID field so it doesn't get lost
    id: Optional[str] = None 

class EngineProfile(BaseModel):
    salary: Decimal; rent: Decimal; current_savings: Decimal

# --- UTILS ---
def to_d(value):
    try: return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except: return Decimal("0.00")

def calculate_financial_health(profile, expenses, assets, liabilities, goals):
    # 1. BASE CALCS
    total_expense = sum(to_d(e.get('amount', 0)) for e in expenses)
    total_debt = sum(l.outstanding_amount for l in liabilities)
    total_emi = sum(l.monthly_payment for l in liabilities)
    
    liquid_assets = profile.current_savings + sum(a.value for a in assets if a.liquidity_score >= 4)
    total_assets = profile.current_savings + sum(a.value for a in assets)
    net_worth = total_assets - total_debt

    actual_burn = profile.rent + total_expense + total_emi
    surplus = profile.salary - actual_burn
    
    # 2. DEBT STRATEGY
    debt_strategy = {"strategy": "None", "freedom_date": "N/A", "recommended_extra_payment": 0}
    
    if liabilities and total_debt > 0:
        max_possible_pay = min(surplus * Decimal("0.5"), total_debt)
        extra = max(Decimal(0), max_possible_pay)
        
        months = 0
        balance = total_debt
        while balance > 0 and months < 120:
            months += 1
            interest = balance * (Decimal("0.15") / 12)
            payment = total_emi + extra
            balance = balance + interest - payment
            if balance < 0: balance = 0
            
        debt_strategy = {
            "strategy": "Avalanche",
            "recommended_extra_payment": float(extra),
            "freedom_date": (datetime.now() + relativedelta(months=months)).strftime("%b %Y")
        }

    # 3. GOAL FEASIBILITY
    analyzed_goals = []
    today = datetime.now()
    available_to_invest = max(Decimal(0), surplus)

    for g in goals:
        try:
            t_date = datetime.strptime(g.target_date, "%Y-%m-%d")
            months_left = (t_date.year - today.year) * 12 + (t_date.month - today.month)
            if months_left <= 0: months_left = 1
        except: months_left = 12
        
        req_monthly = g.target_amount / Decimal(months_left)
        status = "On Track"
        if req_monthly > available_to_invest: status = "At Risk"
        if req_monthly > available_to_invest * 2: status = "Unrealistic"

        analyzed_goals.append({
            **g.dict(), # This now includes the 'id'
            "target_amount": float(g.target_amount),
            "required_monthly": float(req_monthly),
            "months_left": months_left,
            "status": status
        })

    # 4. PROJECTIONS
    projections = []
    curr = net_worth
    for i in range(1, 13):
        curr += surplus
        projections.append({"month": (datetime.now() + relativedelta(months=i)).strftime("%b"), "net_worth": float(curr)})

    # 5. ALLOCATION
    allocation = defaultdict(float)
    if total_assets > 0:
        for a in assets: allocation[a.type] += float(a.value)
        allocation['Cash'] += float(profile.current_savings)
        allocation = {k: round(v/float(total_assets)*100, 1) for k, v in allocation.items()}

    return {
        "score": 75 if surplus > 0 else 30,
        "net_worth": float(net_worth),
        "surplus": float(surplus),
        "monthly_burn": float(actual_burn),
        "recommended_investment": float(min(available_to_invest * Decimal("0.3"), profile.salary * Decimal("0.2"))),
        "emergency_months": float(liquid_assets / max(actual_burn, 1)),
        "debt_strategy": debt_strategy,
        "projections": projections,
        "analyzed_goals": analyzed_goals,
        "allocation": allocation
    }
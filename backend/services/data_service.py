import logging
from datetime import datetime

from database import expenses, assets, liabilities, goals
from services.financial_engine import (
    calculate_financial_health, EngineProfile, EngineAsset, EngineLiability, EngineGoal,
)

log = logging.getLogger(__name__)

RECENT_EXPENSES_LIMIT = 50

FALLBACK_HEALTH = {
    "score": 0, "net_worth": 0, "surplus": 0, "monthly_burn": 0,
    "recommended_investment": 0, "emergency_months": 0,
    "debt_strategy": {"strategy": "None", "freedom_date": "N/A"},
    "projections": [], "analyzed_goals": [], "allocation": {},
}


def serialize(items):
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items


def fetch_user_snapshot(user):
    uname = user["username"]
    month_prefix = datetime.now().strftime("%Y-%m")

    u_expenses = list(expenses.find({"username": uname}).sort("date", -1).limit(RECENT_EXPENSES_LIMIT))
    # Monthly burn must only include this month's expenses, not the last N of all time.
    month_expenses = list(expenses.find(
        {"username": uname, "date": {"$regex": f"^{month_prefix}"}}, {"amount": 1}
    ))
    u_assets = list(assets.find({"username": uname}))
    u_liabs = list(liabilities.find({"username": uname}))
    u_goals = list(goals.find({"username": uname}))

    try:
        profile = EngineProfile(
            salary=user.get("salary", 0),
            rent=user.get("rent", 0),
            current_savings=user.get("current_savings", 0),
        )
        e_assets = [EngineAsset(
            name=a.get("name", ""), type=a.get("type", ""), value=a.get("value", 0),
            liquidity_score=a.get("liquidity_score", 1),
        ) for a in u_assets]
        e_liabs = [EngineLiability(
            name=l.get("name", ""), type=l.get("type", ""),
            outstanding_amount=l.get("outstanding_amount", 0),
            interest_rate=l.get("interest_rate", 0), monthly_payment=l.get("monthly_payment", 0),
        ) for l in u_liabs]
        e_goals = [EngineGoal(
            name=g.get("name", ""), target_amount=g.get("target_amount", 0),
            target_date=g.get("target_date", "2030-01-01"), priority=g.get("priority", "Medium"),
            id=str(g["_id"]),
        ) for g in u_goals]

        health = calculate_financial_health(profile, month_expenses, e_assets, e_liabs, e_goals)
    except Exception:
        log.exception("Financial engine failed for user %s", uname)
        health = dict(FALLBACK_HEALTH)

    final_goals = health.get("analyzed_goals", [])
    if not final_goals and u_goals:
        final_goals = serialize(u_goals)
        for g in final_goals:
            g.setdefault("status", "Pending")

    return {
        "user_profile": {"salary": user.get("salary"), "rent": user.get("rent")},
        "health": health,
        "lists": {
            "expenses": serialize(u_expenses),
            "assets": serialize(u_assets),
            "liabilities": serialize(u_liabs),
            "goals": final_goals,
        },
    }

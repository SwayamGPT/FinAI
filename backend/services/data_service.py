import traceback
# FIX: Use absolute imports assuming running from backend root
from database import expenses, assets, liabilities, goals
from services.financial_engine import calculate_financial_health, EngineProfile, EngineAsset, EngineLiability, EngineGoal

def serialize(items):
    for i in items: i["id"] = str(i["_id"]); del i["_id"]
    return items

def fetch_user_snapshot(user):
    uname = user["username"]
    print(f"\n--- DEBUG: Fetching data for {uname} ---")
    
    # 1. Fetch raw data
    try:
        u_expenses = list(expenses.find({"username": uname}).sort("date", -1).limit(50))
        u_assets = list(assets.find({"username": uname}))
        u_liabs = list(liabilities.find({"username": uname}))
        u_goals = list(goals.find({"username": uname}))
        print(f"DEBUG: Found {len(u_expenses)} expenses, {len(u_assets)} assets, {len(u_liabs)} liabilities")
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        return {}

    # 2. Run Engine
    try:
        profile = EngineProfile(
            salary=user.get("salary", 0), 
            rent=user.get("rent", 0), 
            current_savings=user.get("current_savings", 0)
        )
        
        e_assets = [EngineAsset(name=a.get('name',''), type=a.get('type',''), value=a.get('value',0), liquidity_score=a.get('liquidity_score',1)) for a in u_assets]
        
        e_liabs = [EngineLiability(name=l.get('name',''), type=l.get('type',''), outstanding_amount=l.get('outstanding_amount',0), interest_rate=l.get('interest_rate',0), monthly_payment=l.get('monthly_payment',0)) for l in u_liabs]
        
        e_goals = [EngineGoal(
            name=g.get('name',''), 
            target_amount=g.get('target_amount',0), 
            target_date=g.get('target_date','2030-01-01'), 
            priority=g.get('priority','Medium'),
            id=str(g['_id'])
        ) for g in u_goals]

        print("DEBUG: Running Financial Engine...")
        health = calculate_financial_health(profile, u_expenses, e_assets, e_liabs, e_goals)
        print(f"DEBUG: Engine Success! Score: {health.get('score')}")

    except Exception as e:
        print(f"\n❌ FINANCIAL ENGINE CRASHED ❌")
        print(f"Error: {e}")
        traceback.print_exc() # This prints the EXACT line number of the error
        
        # Fallback to prevent frontend white screen
        health = {
            "score": 0, "net_worth": 0, "surplus": 0, "monthly_burn": 0, 
            "recommended_investment": 0, "emergency_months": 0, 
            "debt_strategy": {"strategy": "None", "freedom_date": "N/A"}, 
            "projections": [], "analyzed_goals": []
        }

    # 3. Handle Goals Fallback
    final_goals = health.get("analyzed_goals", [])
    if not final_goals and u_goals:
        print("DEBUG: Engine failed to analyze goals, returning raw goals.")
        final_goals = serialize(u_goals)
        for g in final_goals: g.setdefault("status", "Pending")

    return {
        "user_profile": {"salary": user.get("salary"), "rent": user.get("rent")},
        "health": health,
        "lists": {
            "expenses": serialize(u_expenses),
            "assets": serialize(u_assets),
            "liabilities": serialize(u_liabs),
            "goals": final_goals
        }
    }
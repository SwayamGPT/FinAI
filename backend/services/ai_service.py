import os
import httpx # Async Client
from datetime import datetime
from database import ai_usage, chats
from utils.security import encrypt_text, decrypt_text

AI_DAILY_LIMIT = 20

def check_rate_limit(username: str) -> bool:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    usage_count = ai_usage.count_documents({
        "username": username,
        "created_at": {"$gte": today_start}
    })
    return usage_count < AI_DAILY_LIMIT

def log_ai_usage(username: str):
    ai_usage.insert_one({"username": username, "created_at": datetime.utcnow()})

def get_ai_context(user_data):
    h = user_data["health"]
    strategy = h.get("debt_strategy", {})
    projections = h.get("projections", [])
    projected_nw = projections[-1]["net_worth"] if projections else 0
    goal_status = ", ".join([f"{g['name']} ({g.get('status','?')})" for g in user_data['lists']['goals']])

    return f"""
    ROLE: Strict Indian Financial Advisor.
    METRICS:
    - Health Score: {h.get('score', 0)}/100
    - Surplus: ₹{h.get('surplus', 0)}
    - Debt Free Date: {strategy.get('freedom_date', 'N/A')}
    - Projected Net Worth (1 Year): ₹{projected_nw}
    - Goals: {goal_status}
    """

def get_chat_history(username: str, limit=6):
    history_doc = chats.find_one({"username": username})
    recent_context = []
    if history_doc:
        for msg in history_doc.get("messages", [])[-limit:]:
            recent_context.append({
                "role": msg["role"], 
                "content": decrypt_text(msg["content"])
            })
    return recent_context

# 🚀 UPGRADE: Store Metadata
def save_chat(username: str, user_query: str, ai_response: str, health_score: int):
    # Simple heuristic to guess topic
    topic = "general"
    if "debt" in user_query.lower() or "loan" in user_query.lower(): topic = "debt"
    elif "invest" in user_query.lower() or "stock" in user_query.lower(): topic = "investment"
    
    new_messages = [
        {"role": "user", "content": encrypt_text(user_query), "timestamp": datetime.utcnow()},
        {
            "role": "ai", 
            "content": encrypt_text(ai_response), 
            "timestamp": datetime.utcnow(),
            "metadata": {
                "health_score_at_time": health_score,
                "topic_guess": topic
            }
        }
    ]
    chats.update_one({"username": username}, {"$push": {"messages": {"$each": new_messages}}}, upsert=True)

# 🚀 UPGRADE: Async Call
async def call_llm(context: str, query: str, history: list):
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key: return "System Error: API Key missing."

    messages = (
        [{"role": "system", "content": context + "\nKeep answers under 3 sentences."}]
        + history
        + [{"role": "user", "content": query}]
    )

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "meta-llama/llama-3-8b-instruct", "messages": messages},
                timeout=15.0
            )
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            else:
                return f"Provider Error ({res.status_code}). Try again."
    except Exception as e:
        print(f"Async LLM Error: {e}")
        return "I am currently offline due to a connection error."
import os, requests
from fastapi import APIRouter, Depends, HTTPException, Header
from datetime import datetime
from collections import defaultdict
import jwt
from database import users, chats
from models import AdvisorRequest
from services.data_service import fetch_user_snapshot
# Import Encryption Utils
from utils.security import encrypt_text, decrypt_text

router = APIRouter()

ai_rate_limit = defaultdict(list)
AI_DAILY_LIMIT = 50 # Increased limit for chat history

def get_current_user(authorization: str = Header(None)):
    if not authorization: raise HTTPException(401, "No Token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        return users.find_one({"username": payload.get("sub")})
    except: raise HTTPException(401, "Invalid Token")

@router.get("/advisor/history")
def get_history(user: dict = Depends(get_current_user)):
    """Fetches encrypted chat history and decrypts it for the user."""
    history = chats.find_one({"username": user["username"]})
    if not history: return []
    
    # Decrypt messages before sending to frontend
    decrypted_msgs = []
    for msg in history.get("messages", []):
        decrypted_msgs.append({
            "role": msg["role"],
            "content": decrypt_text(msg["content"]),
            "timestamp": msg.get("timestamp")
        })
    return decrypted_msgs

@router.post("/advisor")
def advisor(req: AdvisorRequest, user: dict = Depends(get_current_user)):
    if len(req.query) > 1000: raise HTTPException(400, "Query too long")

    # 1. Rate Limit
    today = datetime.now().date()
    ai_rate_limit[user["username"]] = [t for t in ai_rate_limit[user["username"]] if t.date() == today]
    if len(ai_rate_limit[user["username"]]) >= AI_DAILY_LIMIT:
        return {"role": "ai", "content": "Daily limit reached."}

    # 2. Fetch Financial Data (Context)
    data = fetch_user_snapshot(user)
    h = data["health"]
    goal_status = ", ".join([f"{g['name']}" for g in data['lists']['goals']])

    # 3. Get Recent History (Last 5 messages) for Context Awareness
    # We fetch encrypted, decrypt it, and pass to AI so it remembers the conversation
    history_doc = chats.find_one({"username": user["username"]})
    recent_context = []
    if history_doc:
        for msg in history_doc.get("messages", [])[-6:]: # Last 6 messages
            recent_context.append({"role": msg["role"], "content": decrypt_text(msg["content"])})

    system_prompt = f"""
    ROLE: Financial Advisor.
    DATA: Score {h.get('score')}/100. Surplus ₹{h.get('surplus')}. Goals: {goal_status}.
    Keep answers under 3 sentences unless asked for detail.
    """

    messages = [{"role": "system", "content": system_prompt}] + recent_context + [{"role": "user", "content": req.query}]

    # 4. Call AI
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            json={"model": "meta-llama/llama-3-8b-instruct", "messages": messages}
        )
        ai_response = res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"AI Error: {e}")
        return {"role": "ai", "content": "I am offline."}

    # 5. Encrypt & Save to DB
    new_messages = [
        {"role": "user", "content": encrypt_text(req.query), "timestamp": datetime.now()},
        {"role": "ai", "content": encrypt_text(ai_response), "timestamp": datetime.now()}
    ]

    # Upsert: Create document if not exists, otherwise push new messages
    chats.update_one(
        {"username": user["username"]},
        {"$push": {"messages": {"$each": new_messages}}},
        upsert=True
    )

    ai_rate_limit[user["username"]].append(datetime.now())
    return {"role": "ai", "content": ai_response}
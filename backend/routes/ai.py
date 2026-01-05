from fastapi import APIRouter, Depends, HTTPException
from models import AdvisorRequest
from services.data_service import fetch_user_snapshot
# Import updated service functions
from services.ai_service import check_rate_limit, log_ai_usage, get_ai_context, get_chat_history, call_llm, save_chat
# Import Shared Auth
from dependencies import get_current_user

router = APIRouter()

@router.get("/advisor/history")
def get_history_route(auth: dict = Depends(get_current_user)):
    return get_chat_history(auth["user"]["username"], limit=50)

# 🚀 UPGRADE: Now an `async` route
@router.post("/advisor")
async def advisor(req: AdvisorRequest, auth: dict = Depends(get_current_user)):
    user = auth["user"]
    if len(req.query) > 1000: raise HTTPException(400, "Query too long")

    if not check_rate_limit(user["username"]):
        return {"role": "ai", "content": "You have reached your daily limit. Please come back tomorrow!"}

    # Fetch Data
    data = fetch_user_snapshot(user)
    context = get_ai_context(data)
    history = get_chat_history(user["username"])

    # Async AI Call
    ai_response = await call_llm(context, req.query, history)

    # Save with Metadata
    save_chat(user["username"], req.query, ai_response, health_score=data["health"]["score"])
    log_ai_usage(user["username"])

    return {"role": "ai", "content": ai_response}
import os
from fastapi import APIRouter, Depends, HTTPException, Header
from bson import ObjectId
import jwt
from database import users, expenses, assets, liabilities, goals
from models import *
# Correct Import:
from services.data_service import fetch_user_snapshot

router = APIRouter()

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization: raise HTTPException(401, "No Token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        return users.find_one({"username": payload.get("sub")})
    except: raise HTTPException(401, "Invalid Token")

@router.get("/data")
def get_dashboard(user: dict = Depends(get_current_user)):
    return fetch_user_snapshot(user)

# ... (Rest of your CRUD routes for expenses, assets, etc. go here) ...
# Ensure you copy paste the CRUD routes from previous steps if missing!
@router.post("/onboard")
def onboard(data: OnboardingModel, user: dict = Depends(get_current_user)):
    users.update_one({"username": user["username"]}, {"$set": data.dict()})
    return {"msg": "Updated"}

@router.post("/expenses")
def add_e(d: ExpenseModel, u=Depends(get_current_user)): expenses.insert_one({**d.dict(), "username": u["username"]}); return {"msg": "ok"}
@router.delete("/expenses/{id}")
def del_e(id: str, u=Depends(get_current_user)): expenses.delete_one({"_id": ObjectId(id)}); return {"msg": "ok"}

@router.post("/assets")
def add_a(d: AssetModel, u=Depends(get_current_user)): assets.insert_one({**d.dict(), "username": u["username"]}); return {"msg": "ok"}
@router.delete("/assets/{id}")
def del_a(id: str, u=Depends(get_current_user)): assets.delete_one({"_id": ObjectId(id)}); return {"msg": "ok"}

@router.post("/liabilities")
def add_l(d: LiabilityModel, u=Depends(get_current_user)): liabilities.insert_one({**d.dict(), "username": u["username"]}); return {"msg": "ok"}
@router.delete("/liabilities/{id}")
def del_l(id: str, u=Depends(get_current_user)): liabilities.delete_one({"_id": ObjectId(id)}); return {"msg": "ok"}

@router.post("/goals")
def add_g(d: GoalModel, u=Depends(get_current_user)): goals.insert_one({**d.dict(), "username": u["username"]}); return {"msg": "ok"}
@router.delete("/goals/{id}")
def del_g(id: str, u=Depends(get_current_user)): goals.delete_one({"_id": ObjectId(id)}); return {"msg": "ok"}
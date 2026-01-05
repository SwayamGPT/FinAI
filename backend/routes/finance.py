from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database import users, expenses, assets, liabilities, goals
from models import *
from services.data_service import fetch_user_snapshot
# FIX: Use the shared dependency
from dependencies import get_current_user

router = APIRouter()

@router.get("/data")
def get_dashboard(auth: dict = Depends(get_current_user)):
    # Dependency returns {"user": ..., "jti": ..., "token": ...}
    return fetch_user_snapshot(auth["user"])

# --- CRUD ROUTES ---

@router.post("/onboard")
def onboard(data: OnboardingModel, auth: dict = Depends(get_current_user)):
    users.update_one({"username": auth["user"]["username"]}, {"$set": data.dict()})
    return {"msg": "Updated"}

@router.post("/expenses")
def add_e(d: ExpenseModel, auth: dict = Depends(get_current_user)):
    expenses.insert_one({**d.dict(), "username": auth["user"]["username"]})
    return {"msg": "ok"}

@router.delete("/expenses/{id}")
def del_e(id: str, auth: dict = Depends(get_current_user)):
    # Security Fix: Ensure user owns the item
    res = expenses.delete_one({"_id": ObjectId(id), "username": auth["user"]["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "ok"}

@router.post("/assets")
def add_a(d: AssetModel, auth: dict = Depends(get_current_user)):
    assets.insert_one({**d.dict(), "username": auth["user"]["username"]})
    return {"msg": "ok"}

@router.delete("/assets/{id}")
def del_a(id: str, auth: dict = Depends(get_current_user)):
    res = assets.delete_one({"_id": ObjectId(id), "username": auth["user"]["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "ok"}

@router.post("/liabilities")
def add_l(d: LiabilityModel, auth: dict = Depends(get_current_user)):
    liabilities.insert_one({**d.dict(), "username": auth["user"]["username"]})
    return {"msg": "ok"}

@router.delete("/liabilities/{id}")
def del_l(id: str, auth: dict = Depends(get_current_user)):
    res = liabilities.delete_one({"_id": ObjectId(id), "username": auth["user"]["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "ok"}

@router.post("/goals")
def add_g(d: GoalModel, auth: dict = Depends(get_current_user)):
    goals.insert_one({**d.dict(), "username": auth["user"]["username"]})
    return {"msg": "ok"}

@router.delete("/goals/{id}")
def del_g(id: str, auth: dict = Depends(get_current_user)):
    res = goals.delete_one({"_id": ObjectId(id), "username": auth["user"]["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "ok"}
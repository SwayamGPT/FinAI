import os
import jwt
import requests
from datetime import datetime, timedelta
from typing import Optional, Literal
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv
from passlib.context import CryptContext
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from bson import ObjectId
from collections import defaultdict
from jwt import ExpiredSignatureError, InvalidTokenError # Explicit imports

# IMPORT ENGINE
from services.financial_engine import calculate_financial_health

load_dotenv()
app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CONFIG ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
users = db["users"]
expenses = db["expenses"]
assets = db["assets"]
liabilities = db["liabilities"]
goals = db["goals"]

# --- RATE LIMITER ---
ai_rate_limit = defaultdict(list)
AI_DAILY_LIMIT = 20 

@app.on_event("startup")
def create_indexes():
    users.create_index("username", unique=True)
    expenses.create_index([("username", ASCENDING), ("date", DESCENDING)])
    assets.create_index("username")
    liabilities.create_index("username")
    goals.create_index("username")

# --- MODELS ---
class BaseMoneyModel(BaseModel):
    @validator('*', pre=True)
    def round_floats(cls, v):
        if isinstance(v, float): return round(v, 2)
        return v

class UserAuth(BaseModel):
    username: str
    password: str

class GoogleLoginRequest(BaseModel):
    token: str

class OnboardingModel(BaseMoneyModel):
    age: int
    salary: float
    rent: float
    current_savings: float
    saving_goal: str

class AssetModel(BaseMoneyModel):
    name: str
    type: Literal['Bank', 'Mutual Fund', 'Stock', 'Gold', 'Real Estate', 'PF', 'Crypto']
    value: float
    liquidity_score: int = Field(ge=1, le=5)

class LiabilityModel(BaseMoneyModel):
    name: str
    type: Literal['Credit Card', 'Personal Loan', 'Home Loan', 'Car Loan', 'EMI']
    outstanding_amount: float
    interest_rate: float
    monthly_payment: float

class GoalModel(BaseMoneyModel):
    name: str
    target_amount: float
    target_date: str
    priority: Literal['High', 'Medium', 'Low']

class ExpenseModel(BaseMoneyModel):
    title: str
    amount: float
    category: str = "General"
    date: str = datetime.now().strftime("%Y-%m-%d")

class AdvisorRequest(BaseModel):
    query: str

# --- HELPERS ---
def get_password_hash(password): return pwd_context.hash(password)
def verify_password(plain, hashed): return pwd_context.verify(plain, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + timedelta(minutes=30)})
    return jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization: raise HTTPException(401, "Missing Token")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        user = users.find_one({"username": payload.get("sub")})
        if not user: raise HTTPException(401, "User not found")
        return user
    except ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    except Exception:
        raise HTTPException(401, "Authentication failed")

# --- SHARED SNAPSHOT HELPER ---
def fetch_user_snapshot(user):
    uname = user["username"]
    
    u_expenses = list(expenses.find({"username": uname}).sort("date", -1).limit(50))
    u_assets = list(assets.find({"username": uname}))
    u_liabilities = list(liabilities.find({"username": uname}))
    u_goals = list(goals.find({"username": uname}))
    
    def serialize(items):
        for i in items: i["id"] = str(i["_id"]); del i["_id"]
        return items

    serialized_goals = serialize(u_goals)
    health_data = calculate_financial_health(user, u_expenses, u_assets, u_liabilities, serialized_goals)

    return {
        "user_profile": {"salary": user.get("salary", 0), "rent": user.get("rent", 0), "age": user.get("age", 25)},
        "health": health_data,
        "lists": {
            "expenses": serialize(u_expenses),
            "assets": serialize(u_assets),
            "liabilities": serialize(u_liabilities),
            "goals": health_data["analyzed_goals"]
        }
    }

# --- ROUTES ---
@app.post("/register")
def register(user: UserAuth):
    if users.find_one({"username": user.username}): raise HTTPException(400, "Username exists")
    users.insert_one({"username": user.username, "password": get_password_hash(user.password), "salary": 0, "rent": 0})
    return {"message": "Registered"}

@app.post("/login")
def login(user: UserAuth):
    db_user = users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]): raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_access_token({"sub": user.username}), "has_onboarded": db_user.get("salary", 0) > 0}

@app.post("/google-login")
def google_login(request: GoogleLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(request.token, google_requests.Request(), os.getenv("GOOGLE_CLIENT_ID"))
        email = id_info['email']
        user = users.find_one({"username": email})
        if not user:
            users.insert_one({"username": email, "auth_method": "google", "salary": 0, "rent": 0})
            user = users.find_one({"username": email})
        return {"access_token": create_access_token({"sub": email}), "has_onboarded": user.get("salary", 0) > 0}
    except: raise HTTPException(400, "Invalid Google Token")

@app.post("/onboard")
def onboard(data: OnboardingModel, user: dict = Depends(get_current_user)):
    users.update_one({"username": user["username"]}, {"$set": data.dict()})
    return {"message": "Updated"}

@app.get("/data")
def get_dashboard(user: dict = Depends(get_current_user)):
    return fetch_user_snapshot(user)

# --- CRUD OPERATIONS ---
@app.post("/expenses")
def add_exp(item: ExpenseModel, user: dict = Depends(get_current_user)):
    expenses.insert_one({**item.dict(), "username": user["username"]})
    return {"msg": "Added"}

@app.delete("/expenses/{id}")
def del_exp(id: str, user: dict = Depends(get_current_user)):
    res = expenses.delete_one({"_id": ObjectId(id), "username": user["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "Deleted"}

@app.post("/assets")
def add_asset(item: AssetModel, user: dict = Depends(get_current_user)):
    assets.insert_one({**item.dict(), "username": user["username"]})
    return {"msg": "Added"}

@app.delete("/assets/{id}")
def del_asset(id: str, user: dict = Depends(get_current_user)):
    res = assets.delete_one({"_id": ObjectId(id), "username": user["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "Deleted"}

@app.post("/liabilities")
def add_liab(item: LiabilityModel, user: dict = Depends(get_current_user)):
    liabilities.insert_one({**item.dict(), "username": user["username"]})
    return {"msg": "Added"}

@app.delete("/liabilities/{id}")
def del_liab(id: str, user: dict = Depends(get_current_user)):
    res = liabilities.delete_one({"_id": ObjectId(id), "username": user["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "Deleted"}

@app.post("/goals")
def add_goal(item: GoalModel, user: dict = Depends(get_current_user)):
    goals.insert_one({**item.dict(), "username": user["username"]})
    return {"msg": "Added"}

@app.delete("/goals/{id}")
def del_goal(id: str, user: dict = Depends(get_current_user)):
    res = goals.delete_one({"_id": ObjectId(id), "username": user["username"]})
    if res.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"msg": "Deleted"}

# --- ADVISOR ---
@app.post("/advisor")
def advisor(req: AdvisorRequest, user: dict = Depends(get_current_user)):
    if len(req.query) > 500: raise HTTPException(400, "Query too long")

    today = datetime.now().date()
    ai_rate_limit[user["username"]] = [t for t in ai_rate_limit[user["username"]] if t.date() == today]
    
    if len(ai_rate_limit[user["username"]]) >= AI_DAILY_LIMIT:
        raise HTTPException(429, "Daily AI limit reached (20/20)")
    
    data = fetch_user_snapshot(user)
    h = data["health"]
    
    # Truncate context to prevent overflow
    goal_status_str = str([g['name'] + ': ' + g['status'] for g in data['lists']['goals']])
    if len(goal_status_str) > 500: goal_status_str = goal_status_str[:500] + "..."

    context = f"""
    ROLE: Strict Indian Financial Advisor.
    METRICS:
    - Health Score: {h['score']}/100
    - Liquid Emergency Fund: {h['emergency_months']} months
    - Debt Ratio: {h['debt_ratio']}%
    - Recommended Investment: ₹{h['recommended_investment']}
    
    ASSET ALLOCATION: {h['allocation']}
    GOAL STATUS: {goal_status_str}
    USER QUERY: {req.query}
    """
    
    try:
        res = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}"},
            json={"model": "meta-llama/llama-3-8b-instruct:free", "messages": [{"role": "system", "content": context}]}
        )
        ai_rate_limit[user["username"]].append(datetime.now())
        return res.json()["choices"][0]["message"]
    except Exception as e: raise HTTPException(500, str(e))
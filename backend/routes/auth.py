import os, jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from passlib.context import CryptContext
from dotenv import load_dotenv
from database import users
from models import UserAuth, GoogleLoginRequest

load_dotenv()
router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_token(data: dict):
    data.update({"exp": datetime.utcnow() + timedelta(minutes=60)})
    return jwt.encode(data, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

@router.post("/register")
def register(user: UserAuth):
    if users.find_one({"username": user.username}): raise HTTPException(400, "User exists")
    users.insert_one({"username": user.username, "password": pwd_context.hash(user.password), "salary": 0})
    return {"message": "Created"}

@router.post("/login")
def login(user: UserAuth):
    u = users.find_one({"username": user.username})
    if not u or not pwd_context.verify(user.password, u["password"]): raise HTTPException(401, "Invalid")
    return {"access_token": create_token({"sub": user.username}), "has_onboarded": u.get("salary", 0) > 0}

@router.post("/google-login")
def google_login(req: GoogleLoginRequest):
    try:
        # Verify Google Token
        id_info = id_token.verify_oauth2_token(req.token, google_requests.Request(), os.getenv("GOOGLE_CLIENT_ID"))
        email = id_info['email']
        
        # Check or Create User
        user = users.find_one({"username": email})
        if not user:
            users.insert_one({"username": email, "auth": "google", "salary": 0, "rent": 0})
            user = users.find_one({"username": email})
            
        return {"access_token": create_token({"sub": email}), "has_onboarded": user.get("salary", 0) > 0}
    except Exception as e:
        print(f"Google Error: {e}")
        raise HTTPException(400, "Invalid Google Token")
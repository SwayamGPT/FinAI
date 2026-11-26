import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException, Depends
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_MINUTES, GOOGLE_CLIENT_ID
from database import users, token_blacklist
from dependencies import get_current_user
from models import UserAuth, RegisterModel, GoogleLoginRequest
from utils.passwords import hash_password, verify_password

router = APIRouter()


def _now():
    return datetime.now(timezone.utc)


def create_token(subject: str) -> str:
    now = _now()
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "type": "access",
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _new_user(username: str, auth_method: str, **extra) -> dict:
    return {
        "username": username,
        "salary": 0,
        "rent": 0,
        "current_savings": 0,
        "has_onboarded": False,
        "created_at": _now(),
        "auth_method": auth_method,
        **extra,
    }


def _has_onboarded(u: dict) -> bool:
    return bool(u.get("has_onboarded") or u.get("salary", 0) > 0)


@router.post("/register", status_code=201)
def register(user: RegisterModel):
    if users.find_one({"username": user.username}):
        raise HTTPException(400, "User exists")
    users.insert_one(_new_user(user.username, "email", password=hash_password(user.password)))
    return {"message": "Created"}


@router.post("/login")
def login(user: UserAuth):
    u = users.find_one({"username": user.username})
    if not u or not u.get("password") or not verify_password(user.password, u["password"]):
        raise HTTPException(401, "Invalid Credentials")
    return {"access_token": create_token(user.username), "has_onboarded": _has_onboarded(u)}


@router.post("/google-login")
def google_login(req: GoogleLoginRequest):
    try:
        id_info = id_token.verify_oauth2_token(req.token, google_requests.Request(), GOOGLE_CLIENT_ID)
    except Exception:
        raise HTTPException(400, "Invalid Google Token")
    if not id_info.get("email_verified", False):
        raise HTTPException(400, "Google email not verified")

    email = id_info["email"]
    user = users.find_one({"username": email})
    if not user:
        user = _new_user(email, "google")
        users.insert_one(user)
    return {"access_token": create_token(email), "has_onboarded": _has_onboarded(user)}


@router.post("/logout")
def logout(auth: dict = Depends(get_current_user)):
    # Upsert so double-clicks don't raise duplicate key errors.
    token_blacklist.update_one(
        {"jti": auth["jti"]},
        {"$set": {"jti": auth["jti"], "createdAt": _now()}},
        upsert=True,
    )
    return {"message": "Logged out successfully"}

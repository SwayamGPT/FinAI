from fastapi import Header, HTTPException
import jwt
import os
from database import users, token_blacklist

def get_current_user(authorization: str = Header(None)):
    if not authorization: raise HTTPException(401, "No Token")
    try:
        token = authorization.split(" ")[1]
        
        # 1. Decode FIRST to get JTI
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        jti = payload.get("jti")

        # 2. Check Blacklist using JTI (Faster & Cleaner)
        if token_blacklist.find_one({"jti": jti}):
            raise HTTPException(401, "Session Revoked (Logged Out)")

        # 3. Get User
        user = users.find_one({"username": payload.get("sub")})
        if not user: raise HTTPException(401, "User Not Found")
        
        return {"user": user, "jti": jti, "token": token}

    except jwt.ExpiredSignatureError: raise HTTPException(401, "Token Expired")
    except jwt.InvalidTokenError: raise HTTPException(401, "Invalid Token")
    except Exception: raise HTTPException(401, "Auth Failed")
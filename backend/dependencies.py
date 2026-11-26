import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Header, HTTPException

from config import SECRET_KEY, ALGORITHM
from database import users, token_blacklist


def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "No Token")
    token = authorization.split(" ", 1)[1].strip()

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token Expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid Token")

    jti = payload.get("jti")
    if not jti or token_blacklist.find_one({"jti": jti}):
        raise HTTPException(401, "Session Revoked (Logged Out)")

    user = users.find_one({"username": payload.get("sub")})
    if not user:
        raise HTTPException(401, "User Not Found")

    return {"user": user, "jti": jti, "token": token}


def parse_object_id(id: str) -> ObjectId:
    try:
        return ObjectId(id)
    except (InvalidId, TypeError):
        raise HTTPException(404, "Not found")

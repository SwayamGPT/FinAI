import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

users = db["users"]
expenses = db["expenses"]
assets = db["assets"]
liabilities = db["liabilities"]
goals = db["goals"]
chats = db["chats"]
ai_usage = db["ai_usage"]
token_blacklist = db["token_blacklist"] # NEW: Logout support

# Indexes
ai_usage.create_index([("username", 1), ("created_at", 1)])
ai_usage.create_index("created_at", expireAfterSeconds=86400)
token_blacklist.create_index("createdAt", expireAfterSeconds=3600) # Auto-clear expired tokens
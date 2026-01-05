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
chats = db["chats"] # NEW: Stores chat history
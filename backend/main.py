from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, finance, ai 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚀 UPGRADE: Versioning
app.include_router(auth.router, prefix="/v1/auth")
app.include_router(finance.router, prefix="/v1/finance")
app.include_router(ai.router, prefix="/v1/ai")


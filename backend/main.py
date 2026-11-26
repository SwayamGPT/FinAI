import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, SECRET_KEY
from routes import auth, finance, ai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")

app = FastAPI(title="FinAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/v1/auth")
app.include_router(finance.router, prefix="/v1/finance")
app.include_router(ai.router, prefix="/v1/ai")


@app.get("/health")
def health():
    return {"status": "ok"}

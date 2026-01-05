from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Import the separated routes
from routes import auth, finance, ai 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect Routes
app.include_router(auth.router)
app.include_router(finance.router)
app.include_router(ai.router) # AI is now its own module!
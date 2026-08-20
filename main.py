# main.py

from fastapi import FastAPI
from routes.transactions import router as transaction_router
from routes.auth import router as auth_router

app = FastAPI(
    title="SecureFlow-AI",
    description="Real-time AI-driven UPI fraud prevention API",
    version="1.0.0"
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(transaction_router, prefix="/api/transactions")


@app.get("/")
def root():
    return {
        "project": "SecureFlow-AI",
        "status": "running",
        "message": "Real-time UPI fraud detection backend"
    }
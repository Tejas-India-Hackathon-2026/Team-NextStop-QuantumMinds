from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# =========================================================
# SECUREFLOW-AI BACKEND
# CODE 1 — SERVER SETUP
# =========================================================


# Create FastAPI application
app = FastAPI(
    title="SecureFlow-AI",
    description="AI-driven real-time UPI fraud prevention system",
    version="1.0.0"
)


# =========================================================
# FRONTEND CONNECTION
# =========================================================

# This allows your React / Next.js frontend
# to communicate with the backend.

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]
)


# =========================================================
# HOME API
# =========================================================

@app.get("/")
def home():

    return {
        "project": "SecureFlow-AI",
        "status": "Backend is running",
        "message": "AI fraud detection server is online"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    return {
        "status": "online",
        "service": "SecureFlow-AI"
    }


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
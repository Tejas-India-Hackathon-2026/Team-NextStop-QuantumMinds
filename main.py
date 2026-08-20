from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
from datetime import datetime


# =========================================================
# SECUREFLOW-AI BACKEND
# CODE 4 — TRANSACTION API
# =========================================================


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="SecureFlow-AI",
    description="AI-driven real-time UPI fraud prevention system",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# DATABASE
# =========================================================

DATABASE_NAME = "secureflow.db"


def get_database():

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    connection = get_database()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT UNIQUE NOT NULL,

            name TEXT NOT NULL,

            average_amount REAL DEFAULT 0,

            known_device TEXT,

            known_location TEXT,

            known_beneficiary TEXT,

            total_transactions INTEGER DEFAULT 0

        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT NOT NULL,

            amount REAL NOT NULL,

            device TEXT,

            location TEXT,

            beneficiary TEXT,

            transaction_time TEXT,

            risk_score REAL,

            risk_level TEXT,

            decision TEXT,

            reasons TEXT,

            created_at TEXT

        )
    """)

    connection.commit()

    connection.close()


create_database()


# =========================================================
# DEMO USER
# =========================================================

def create_demo_user():

    connection = get_database()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        ("USER001",)
    )

    user = cursor.fetchone()

    if user is None:

        cursor.execute(
            """
            INSERT INTO users (

                user_id,
                name,
                average_amount,
                known_device,
                known_location,
                known_beneficiary,
                total_transactions

            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,

            (
                "USER001",
                "Demo User",
                1200.0,
                "Android-Primary",
                "Kolkata",
                "rahul@upi",
                42
            )
        )

        connection.commit()

    connection.close()


create_demo_user()


# =========================================================
# TRANSACTION REQUEST MODEL
# =========================================================

class TransactionRequest(BaseModel):

    user_id: str = "USER001"

    amount: float = Field(
        gt=0,
        description="Transaction amount in INR"
    )

    device: str

    location: str

    beneficiary: str

    transaction_time: str

    recent_transactions: int = Field(
        default=0,
        ge=0
    )


# =========================================================
# GET USER PROFILE
# =========================================================

def get_user_profile(user_id):

    connection = get_database()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    return user


# =========================================================
# TRANSACTION API
# =========================================================

@app.post("/api/transaction")
def receive_transaction(
    transaction: TransactionRequest
):

    # -----------------------------------------------------
    # STEP 1 — FIND USER
    # -----------------------------------------------------

    user = get_user_profile(
        transaction.user_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User profile not found"
        )


    # -----------------------------------------------------
    # STEP 2 — PREPARE TRANSACTION
    # -----------------------------------------------------

    transaction_data = {

        "user_id":
            transaction.user_id,

        "amount":
            transaction.amount,

        "device":
            transaction.device,

        "location":
            transaction.location,

        "beneficiary":
            transaction.beneficiary,

        "transaction_time":
            transaction.transaction_time,

        "recent_transactions":
            transaction.recent_transactions
    }


    # -----------------------------------------------------
    # STEP 3 — COMPARE WITH USER PROFILE
    # -----------------------------------------------------

    profile_comparison = {

        "amount_difference":
            transaction.amount -
            user["average_amount"],

        "new_device":
            transaction.device !=
            user["known_device"],

        "new_location":
            transaction.location !=
            user["known_location"],

        "new_beneficiary":
            transaction.beneficiary !=
            user["known_beneficiary"]

    }


    # -----------------------------------------------------
    # STEP 4 — RETURN TRANSACTION
    # -----------------------------------------------------

    return {

        "success": True,

        "message":
            "Transaction received successfully",

        "transaction":
            transaction_data,

        "user_profile": {

            "user_id":
                user["user_id"],

            "name":
                user["name"],

            "average_amount":
                user["average_amount"],

            "known_device":
                user["known_device"],

            "known_location":
                user["known_location"],

            "known_beneficiary":
                user["known_beneficiary"]

        },

        "comparison":
            profile_comparison,

        "next_step":
            "Send transaction to behavioural analysis engine"

    }


# =========================================================
# GET USER PROFILE
# =========================================================

@app.get("/api/user/{user_id}")
def get_user(user_id: str):

    user = get_user_profile(
        user_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {

        "success": True,

        "user": dict(user)

    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    connection = get_database()

    connection.execute(
        "SELECT 1"
    )

    connection.close()

    return {

        "status":
            "online",

        "database":
            "online",

        "module":
            "Transaction API"

    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {

        "project":
            "SecureFlow-AI",

        "status":
            "Backend is running",

        "module":
            "Transaction API"

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
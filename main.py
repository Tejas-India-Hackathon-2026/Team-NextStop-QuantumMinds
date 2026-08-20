from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3


# =========================================================
# SECUREFLOW-AI BACKEND
# CODE 3 — USER PROFILE & BEHAVIOURAL DATA
# =========================================================


# =========================================================
# FASTAPI SERVER
# =========================================================

app = FastAPI(
    title="SecureFlow-AI",
    description="AI-driven real-time UPI fraud prevention system",
    version="1.0.0"
)


# =========================================================
# FRONTEND CONNECTION
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

    # USERS TABLE
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

    # TRANSACTIONS TABLE
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
# DEMO USER PROFILE
# =========================================================

def create_demo_user():

    connection = get_database()

    cursor = connection.cursor()

    # Check whether USER001 already exists
    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        ("USER001",)
    )

    existing_user = cursor.fetchone()

    # Only create user if it doesn't exist
    if existing_user is None:

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
# USER PROFILE API
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

        "user": {

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
                user["known_beneficiary"],

            "total_transactions":
                user["total_transactions"]

        }

    }


# =========================================================
# ADD NEW USER
# =========================================================

@app.post("/api/user")
def create_user(

    user_id: str,
    name: str,
    average_amount: float = 0,
    known_device: str = "",
    known_location: str = "",
    known_beneficiary: str = ""

):

    connection = get_database()

    cursor = connection.cursor()

    # Check if user already exists
    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    existing_user = cursor.fetchone()

    if existing_user:

        connection.close()

        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # Insert new user
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
            user_id,
            name,
            average_amount,
            known_device,
            known_location,
            known_beneficiary,
            0
        )
    )

    connection.commit()

    connection.close()

    return {

        "success": True,

        "message":
            "User profile created",

        "user_id":
            user_id

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
            "User Profile"

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
            "User Profile"

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
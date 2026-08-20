from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3


# =========================================================
# SECUREFLOW-AI BACKEND
# CODE 2 — DATABASE CONNECTION
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
# DATABASE CONFIGURATION
# =========================================================

DATABASE_NAME = "secureflow.db"


# =========================================================
# DATABASE CONNECTION FUNCTION
# =========================================================

def get_database():

    connection = sqlite3.connect(
        DATABASE_NAME
    )

    # Allows us to access database rows
    # using column names.
    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def create_database():

    connection = get_database()

    cursor = connection.cursor()


    # -----------------------------------------------------
    # USERS TABLE
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # TRANSACTIONS TABLE
    # -----------------------------------------------------

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


# =========================================================
# INITIALIZE DATABASE
# =========================================================

create_database()


# =========================================================
# HOME API
# =========================================================

@app.get("/")
def home():

    return {

        "project": "SecureFlow-AI",

        "status": "Backend is running",

        "database": "Connected"

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

        "status": "online",

        "service": "SecureFlow-AI",

        "database": "online"

    }


# =========================================================
# DATABASE TEST API
# =========================================================

@app.get("/database-test")
def database_test():

    connection = get_database()

    cursor = connection.cursor()


    # Check tables
    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
    """)

    tables = cursor.fetchall()

    connection.close()


    return {

        "database": DATABASE_NAME,

        "status": "connected",

        "tables": [
            table["name"]
            for table in tables
        ]

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
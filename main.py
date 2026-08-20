# ============================================================
# SECUREFLOW-AI
# Tejas India Hackathon Prototype
#
# FastAPI Backend
# Behaviour + ML + Graph Risk + Dynamic Verification
# ============================================================

import os
import json
import sqlite3
import random
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sklearn.ensemble import RandomForestClassifier


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE = "secureflow.db"

app = FastAPI(
    title="SecureFlow-AI API",
    description="Real-time AI-driven UPI fraud prevention prototype",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            avg_transaction REAL DEFAULT 0,

            known_device TEXT DEFAULT '',

            known_location TEXT DEFAULT '',

            known_beneficiary TEXT DEFAULT '',

            total_transactions INTEGER DEFAULT 0,

            successful_transactions INTEGER DEFAULT 0

        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id TEXT,

            amount REAL,

            device TEXT,

            location TEXT,

            beneficiary TEXT,

            transaction_time TEXT,

            risk_score REAL,

            behaviour_score REAL,

            ml_score REAL,

            graph_score REAL,

            risk_level TEXT,

            decision TEXT,

            reasons TEXT,

            verified INTEGER DEFAULT 0,

            created_at TEXT

        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS relationships (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sender TEXT,

            beneficiary TEXT,

            transaction_count INTEGER DEFAULT 0,

            suspicious_count INTEGER DEFAULT 0

        )
    """)

    db.commit()

    db.close()


initialize_database()


# ============================================================
# DEMO USER
# ============================================================

def create_demo_user():

    db = get_db()

    existing = db.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        ("USER001",)
    ).fetchone()

    if not existing:

        db.execute(
            """
            INSERT INTO users (
                user_id,
                name,
                avg_transaction,
                known_device,
                known_location,
                known_beneficiary,
                total_transactions,
                successful_transactions
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,

            (
                "USER001",
                "Demo User",
                1200,
                "Android-Primary",
                "Kolkata",
                "rahul@upi",
                42,
                41
            )
        )

        db.commit()

    db.close()


create_demo_user()


# ============================================================
# API MODELS
# ============================================================

class TransactionRequest(BaseModel):

    user_id: str = "USER001"

    amount: float = Field(gt=0)

    device: str

    location: str

    beneficiary: str

    transaction_time: str

    recent_transactions: int = Field(
        default=1,
        ge=0
    )


class VerificationRequest(BaseModel):

    transaction_id: int

    answer: str


# ============================================================
# SYNTHETIC ML DATA
# ============================================================

FEATURES = [

    "amount_ratio",

    "new_device",

    "new_location",

    "new_beneficiary",

    "unusual_time",

    "transaction_frequency",

    "graph_risk"

]


def generate_training_data():

    np.random.seed(42)

    rows = []

    for _ in range(6000):

        amount_ratio = np.random.uniform(
            0.1,
            12
        )

        new_device = np.random.binomial(
            1,
            0.15
        )

        new_location = np.random.binomial(
            1,
            0.15
        )

        new_beneficiary = np.random.binomial(
            1,
            0.12
        )

        unusual_time = np.random.binomial(
            1,
            0.10
        )

        transaction_frequency = np.random.poisson(
            2
        )

        graph_risk = np.random.uniform(
            0,
            1
        )

        risk = 0

        if amount_ratio > 5:
            risk += 3

        elif amount_ratio > 3:
            risk += 2

        elif amount_ratio > 2:
            risk += 1

        risk += new_device * 2

        risk += new_location * 2

        risk += new_beneficiary * 2

        risk += unusual_time * 2

        if transaction_frequency > 5:
            risk += 2

        if graph_risk > 0.7:
            risk += 3

        fraud = 1 if risk >= 5 else 0

        rows.append([
            amount_ratio,
            new_device,
            new_location,
            new_beneficiary,
            unusual_time,
            transaction_frequency,
            graph_risk,
            fraud
        ])

    return pd.DataFrame(
        rows,
        columns=FEATURES + ["fraud"]
    )


def train_model():

    data = generate_training_data()

    X = data[FEATURES]

    y = data["fraud"]

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(
        X,
        y
    )

    return model


MODEL = train_model()


# ============================================================
# USER PROFILE
# ============================================================

def get_user_profile(user_id):

    db = get_db()

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    db.close()

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return dict(user)


# ============================================================
# BEHAVIOURAL ANALYSIS
# ============================================================

def behavioural_analysis(
    transaction,
    user
):

    score = 0

    reasons = []

    avg = max(
        user["avg_transaction"],
        1
    )

    amount_ratio = (
        transaction.amount / avg
    )

    # Amount anomaly
    if amount_ratio >= 10:

        score += 30

        reasons.append(
            "Transaction amount is extremely higher than the user's normal behaviour."
        )

    elif amount_ratio >= 5:

        score += 22

        reasons.append(
            "Transaction amount is significantly higher than the user's normal behaviour."
        )

    elif amount_ratio >= 3:

        score += 15

        reasons.append(
            "Transaction amount is considerably higher than usual."
        )

    elif amount_ratio >= 2:

        score += 8

        reasons.append(
            "Transaction amount is moderately higher than usual."
        )

    # Device
    if transaction.device != user["known_device"]:

        score += 18

        reasons.append(
            "Transaction originated from a new device."
        )

    # Location
    if transaction.location != user["known_location"]:

        score += 15

        reasons.append(
            "Transaction originated from a new location."
        )

    # Beneficiary
    if transaction.beneficiary != user["known_beneficiary"]:

        score += 12

        reasons.append(
            "New beneficiary detected."
        )

    # Time
    try:

        time = datetime.strptime(
            transaction.transaction_time,
            "%I:%M %p"
        )

        if time.hour >= 23 or time.hour < 5:

            score += 15

            reasons.append(
                "Transaction occurred during an unusual time."
            )

    except Exception:

        pass

    # Frequency
    if transaction.recent_transactions >= 6:

        score += 15

        reasons.append(
            "Unusually high transaction frequency detected."
        )

    elif transaction.recent_transactions >= 4:

        score += 8

        reasons.append(
            "Transaction frequency is above normal."
        )

    return min(score, 100), reasons


# ============================================================
# GRAPH RISK
# ============================================================

def calculate_graph_risk(
    user_id,
    beneficiary
):

    db = get_db()

    relationship = db.execute(
        """
        SELECT *
        FROM relationships

        WHERE sender = ?
        AND beneficiary = ?
        """,
        (
            user_id,
            beneficiary
        )
    ).fetchone()

    db.close()

    # New relationship
    if not relationship:

        return 25

    transaction_count = relationship[
        "transaction_count"
    ]

    suspicious_count = relationship[
        "suspicious_count"
    ]

    if transaction_count == 0:

        return 25

    suspicious_ratio = (
        suspicious_count /
        transaction_count
    )

    return round(
        suspicious_ratio * 100,
        2
    )


# ============================================================
# ML RISK
# ============================================================

def calculate_ml_risk(
    transaction,
    user,
    graph_score
):

    amount_ratio = (
        transaction.amount /
        max(user["avg_transaction"], 1)
    )

    new_device = int(
        transaction.device !=
        user["known_device"]
    )

    new_location = int(
        transaction.location !=
        user["known_location"]
    )

    new_beneficiary = int(
        transaction.beneficiary !=
        user["known_beneficiary"]
    )

    try:

        time = datetime.strptime(
            transaction.transaction_time,
            "%I:%M %p"
        )

        unusual_time = int(
            time.hour >= 23 or
            time.hour < 5
        )

    except Exception:

        unusual_time = 0

    X = pd.DataFrame(
        [[
            amount_ratio,
            new_device,
            new_location,
            new_beneficiary,
            unusual_time,
            transaction.recent_transactions,
            graph_score / 100
        ]],
        columns=FEATURES
    )

    probability = MODEL.predict_proba(
        X
    )[0][1]

    return round(
        probability * 100,
        2
    )


# ============================================================
# DYNAMIC VERIFICATION QUESTIONS
# ============================================================

def generate_question(
    transaction,
    user,
    risk_score
):

    questions = []

    if transaction.device != user["known_device"]:

        questions.append({
            "type": "device",
            "question":
                "Are you currently using a new device to make this payment?",
            "answer": "YES"
        })

    if transaction.beneficiary != user["known_beneficiary"]:

        questions.append({
            "type": "beneficiary",
            "question":
                "Did you intentionally add this new beneficiary?",
            "answer": "YES"
        })

    if transaction.amount > user["avg_transaction"] * 3:

        questions.append({
            "type": "amount",
            "question":
                "Did you personally initiate this high-value payment?",
            "answer": "YES"
        })

    if transaction.location != user["known_location"]:

        questions.append({
            "type": "location",
            "question":
                "Are you currently making this payment from a new location?",
            "answer": "YES"
        })

    if not questions:

        questions.append({
            "type": "confirmation",
            "question":
                "Did you personally initiate this transaction?",
            "answer": "YES"
        })

    return random.choice(questions)


# ============================================================
# DECISION
# ============================================================

def get_decision(score):

    # According to your architecture slide:
    # 0-30     = ALLOW
    # 31-70    = ALERT
    # 71-100   = BLOCK

    if score <= 30:

        return "ALLOW", "LOW"

    elif score <= 70:

        return "ALERT", "MEDIUM"

    else:

        return "BLOCK", "HIGH"


# ============================================================
# ANALYZE TRANSACTION
# ============================================================

@app.post("/api/analyze")
def analyze_transaction(
    transaction: TransactionRequest
):

    user = get_user_profile(
        transaction.user_id
    )

    # Behaviour
    behaviour_score, reasons = (
        behavioural_analysis(
            transaction,
            user
        )
    )

    # Graph
    graph_score = calculate_graph_risk(
        transaction.user_id,
        transaction.beneficiary
    )

    # ML
    ml_score = calculate_ml_risk(
        transaction,
        user,
        graph_score
    )

    # Hybrid risk
    final_score = round(
        (
            behaviour_score * 0.45
            +
            ml_score * 0.35
            +
            graph_score * 0.20
        ),
        2
    )

    final_score = min(
        max(final_score, 0),
        100
    )

    decision, risk_level = get_decision(
        final_score
    )

    # Verification
    verification = None

    if decision == "ALERT":

        verification = generate_question(
            transaction,
            user,
            final_score
        )

    # Save transaction
    db = get_db()

    cursor = db.execute(
        """
        INSERT INTO transactions (

            user_id,
            amount,
            device,
            location,
            beneficiary,
            transaction_time,
            risk_score,
            behaviour_score,
            ml_score,
            graph_score,
            risk_level,
            decision,
            reasons,
            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            transaction.user_id,
            transaction.amount,
            transaction.device,
            transaction.location,
            transaction.beneficiary,
            transaction.transaction_time,
            final_score,
            behaviour_score,
            ml_score,
            graph_score,
            risk_level,
            decision,
            json.dumps(reasons),
            datetime.now().isoformat()
        )
    )

    transaction_id = cursor.lastrowid

    # Update relationship graph
    db.execute(
        """
        INSERT INTO relationships (
            sender,
            beneficiary,
            transaction_count,
            suspicious_count
        )

        VALUES (?, ?, 1, ?)

        ON CONFLICT(id) DO NOTHING
        """,
        (
            transaction.user_id,
            transaction.beneficiary,
            1 if decision != "ALLOW" else 0
        )
    )

    # The above works for insertion but not logical
    # sender+beneficiary uniqueness, so update manually.

    relationship = db.execute(
        """
        SELECT id
        FROM relationships
        WHERE sender = ?
        AND beneficiary = ?
        """,
        (
            transaction.user_id,
            transaction.beneficiary
        )
    ).fetchone()

    if relationship:

        db.execute(
            """
            UPDATE relationships

            SET transaction_count =
                    transaction_count + 1,

                suspicious_count =
                    suspicious_count + ?

            WHERE id = ?
            """,
            (
                1 if decision != "ALLOW" else 0,
                relationship["id"]
            )
        )

    else:

        db.execute(
            """
            INSERT INTO relationships (
                sender,
                beneficiary,
                transaction_count,
                suspicious_count
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                transaction.user_id,
                transaction.beneficiary,
                1,
                1 if decision != "ALLOW" else 0
            )
        )

    db.commit()

    db.close()

    return {

        "success": True,

        "transaction_id": transaction_id,

        "risk": {

            "score": final_score,

            "behaviour_score":
                behaviour_score,

            "ml_score":
                ml_score,

            "graph_score":
                graph_score,

            "level":
                risk_level
        },

        "decision": decision,

        "reasons": reasons,

        "verification": verification

    }


# ============================================================
# VERIFICATION
# ============================================================

@app.post("/api/verify")
def verify_transaction(
    request: VerificationRequest
):

    db = get_db()

    transaction = db.execute(
        """
        SELECT *
        FROM transactions
        WHERE id = ?
        """,
        (request.transaction_id,)
    ).fetchone()

    db.close()

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    # Prototype verification:
    # The generated questions expect YES.
    if request.answer.upper() == "YES":

        db = get_db()

        db.execute(
            """
            UPDATE transactions

            SET verified = 1,
                decision = 'ALLOW',
                risk_level = 'LOW'

            WHERE id = ?
            """,
            (request.transaction_id,)
        )

        db.commit()
        db.close()

        return {
            "success": True,
            "verified": True,
            "decision": "ALLOW",
            "message":
                "Verification successful. Transaction allowed."
        }

    return {

        "success": True,

        "verified": False,

        "decision": "BLOCK",

        "message":
            "Verification failed. Transaction blocked."
    }


# ============================================================
# USER PROFILE
# ============================================================

@app.get("/api/user/{user_id}")
def user_profile(
    user_id: str
):

    return get_user_profile(
        user_id
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.get("/api/transactions/{user_id}")
def transaction_history(
    user_id: str
):

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM transactions

        WHERE user_id = ?

        ORDER BY id DESC

        LIMIT 50
        """,
        (user_id,)
    ).fetchall()

    db.close()

    return {
        "success": True,
        "transactions": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/api/health")
def health():

    return {

        "status": "online",

        "service":
            "SecureFlow-AI",

        "features": [
            "Behavioural Analysis",
            "Machine Learning",
            "Graph Risk",
            "Dynamic Verification",
            "Risk Scoring",
            "Allow Alert Block"
        ]
    }


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000
    )
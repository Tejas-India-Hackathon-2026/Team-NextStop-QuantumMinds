from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
from datetime import datetime


# =========================================================
# SECUREFLOW-AI
# FINAL BACKEND SERVER
# =========================================================


app = FastAPI(
    title="SecureFlow-AI",
    description="AI-driven real-time transaction fraud prevention system",
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

DATABASE = "secureflow.db"


def get_db():

    db = sqlite3.connect(DATABASE)

    db.row_factory = sqlite3.Row

    return db


def create_database():

    db = get_db()

    db.execute("""
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

    db.execute("""
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

    db.commit()
    db.close()


create_database()


# =========================================================
# DEMO USER
# =========================================================

def create_demo_user():

    db = get_db()

    user = db.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        ("USER001",)
    ).fetchone()

    if user is None:

        db.execute("""
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
        """, (
            "USER001",
            "Demo User",
            1200.0,
            "Android-Primary",
            "Kolkata",
            "rahul@upi",
            42
        ))

        db.commit()

    db.close()


create_demo_user()


# =========================================================
# REQUEST MODELS
# =========================================================

class TransactionRequest(BaseModel):

    user_id: str

    amount: float = Field(gt=0)

    device: str

    location: str

    beneficiary: str

    transaction_time: str

    recent_transactions: int = Field(
        default=0,
        ge=0
    )


class VerificationRequest(BaseModel):

    transaction_id: int

    confirmed: bool


# =========================================================
# USER PROFILE
# =========================================================

def get_user(user_id):

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

    return user


# =========================================================
# RISK ANALYSIS
# =========================================================

def calculate_risk(
    transaction,
    user
):

    score = 0

    reasons = []


    # -----------------------------------------------------
    # AMOUNT
    # -----------------------------------------------------

    average = user["average_amount"]

    if average > 0:

        ratio = transaction.amount / average

        if ratio >= 10:

            score += 30

            reasons.append(
                "Transaction amount is extremely high compared with normal behaviour."
            )

        elif ratio >= 5:

            score += 25

            reasons.append(
                "Transaction amount is significantly higher than normal."
            )

        elif ratio >= 3:

            score += 18

            reasons.append(
                "Transaction amount is considerably higher than normal."
            )

        elif ratio >= 2:

            score += 10

            reasons.append(
                "Transaction amount is higher than normal."
            )


    # -----------------------------------------------------
    # DEVICE
    # -----------------------------------------------------

    if transaction.device != user["known_device"]:

        score += 20

        reasons.append(
            "Unknown device detected."
        )


    # -----------------------------------------------------
    # LOCATION
    # -----------------------------------------------------

    if transaction.location != user["known_location"]:

        score += 15

        reasons.append(
            "Unusual location detected."
        )


    # -----------------------------------------------------
    # BENEFICIARY
    # -----------------------------------------------------

    if transaction.beneficiary != user["known_beneficiary"]:

        score += 15

        reasons.append(
            "New beneficiary detected."
        )


    # -----------------------------------------------------
    # FREQUENCY
    # -----------------------------------------------------

    if transaction.recent_transactions >= 8:

        score += 15

        reasons.append(
            "Very high transaction frequency detected."
        )

    elif transaction.recent_transactions >= 5:

        score += 8

        reasons.append(
            "Higher-than-normal transaction frequency detected."
        )


    # -----------------------------------------------------
    # UNUSUAL TIME
    # -----------------------------------------------------

    try:

        time = datetime.strptime(
            transaction.transaction_time,
            "%I:%M %p"
        )

        if time.hour >= 23 or time.hour < 5:

            score += 15

            reasons.append(
                "Transaction occurred during unusual hours."
            )

    except ValueError:

        pass


    score = min(score, 100)


    # -----------------------------------------------------
    # RISK LEVEL
    # -----------------------------------------------------

    if score <= 30:

        level = "LOW"

    elif score <= 70:

        level = "MEDIUM"

    else:

        level = "HIGH"


    return score, level, reasons


# =========================================================
# DECISION ENGINE
# =========================================================

def make_decision(score):

    if score <= 30:

        return "ALLOW"

    elif score <= 70:

        return "ALERT"

    else:

        return "BLOCK"


# =========================================================
# VERIFICATION QUESTION
# =========================================================

def generate_verification(
    transaction,
    user
):

    if transaction.device != user["known_device"]:

        return (
            "Are you currently using a new device?"
        )

    if transaction.location != user["known_location"]:

        return (
            "Are you currently making this transaction from a new location?"
        )

    if transaction.beneficiary != user["known_beneficiary"]:

        return (
            "Did you intentionally make this payment to this new beneficiary?"
        )

    if transaction.amount > user["average_amount"] * 3:

        return (
            "Did you personally initiate this high-value transaction?"
        )

    return (
        "Did you personally initiate this transaction?"
    )


# =========================================================
# MAIN TRANSACTION API
# =========================================================

@app.post("/api/transaction")
def analyze_transaction(
    transaction: TransactionRequest
):

    # -----------------------------------------------------
    # FIND USER
    # -----------------------------------------------------

    user = get_user(
        transaction.user_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    # -----------------------------------------------------
    # RISK ANALYSIS
    # -----------------------------------------------------

    score, level, reasons = calculate_risk(
        transaction,
        user
    )


    # -----------------------------------------------------
    # DECISION
    # -----------------------------------------------------

    decision = make_decision(score)


    # -----------------------------------------------------
    # VERIFICATION
    # -----------------------------------------------------

    verification = None

    if decision == "ALERT":

        verification = generate_verification(
            transaction,
            user
        )


    # -----------------------------------------------------
    # SAVE TRANSACTION
    # -----------------------------------------------------

    db = get_db()

    cursor = db.execute("""
        INSERT INTO transactions (

            user_id,
            amount,
            device,
            location,
            beneficiary,
            transaction_time,
            risk_score,
            risk_level,
            decision,
            reasons,
            created_at

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

    """, (

        transaction.user_id,
        transaction.amount,
        transaction.device,
        transaction.location,
        transaction.beneficiary,
        transaction.transaction_time,
        score,
        level,
        decision,
        " | ".join(reasons),
        datetime.now().isoformat()

    ))

    transaction_id = cursor.lastrowid

    db.commit()

    db.close()


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "success": True,

        "transaction_id":
            transaction_id,

        "risk": {

            "score":
                score,

            "level":
                level,

            "reasons":
                reasons

        },

        "decision":
            decision,

        "verification":
            verification

    }


# =========================================================
# VERIFICATION API
# =========================================================

@app.post("/api/verification")
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


    if transaction is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    if request.confirmed:

        decision = "ALLOW"

        message = (
            "Transaction verified by user and allowed."
        )

    else:

        decision = "BLOCK"

        message = (
            "Transaction rejected by user and blocked."
        )


    db.execute(
        """
        UPDATE transactions
        SET decision = ?
        WHERE id = ?
        """,
        (
            decision,
            request.transaction_id
        )
    )

    db.commit()

    db.close()


    return {

        "success": True,

        "transaction_id":
            request.transaction_id,

        "decision":
            decision,

        "message":
            message

    }


# =========================================================
# TRANSACTION HISTORY
# =========================================================

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


# =========================================================
# ALERTS
# =========================================================

@app.get("/api/alerts/{user_id}")
def alerts(
    user_id: str
):

    db = get_db()

    rows = db.execute(
        """
        SELECT *
        FROM transactions

        WHERE user_id = ?

        AND (
            risk_level = 'HIGH'
            OR decision = 'ALERT'
            OR decision = 'BLOCK'
        )

        ORDER BY id DESC

        LIMIT 20
        """,
        (user_id,)
    ).fetchall()

    db.close()


    return {

        "success": True,

        "alerts": [
            dict(row)
            for row in rows
        ]

    }


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/api/dashboard/{user_id}")
def dashboard(
    user_id: str
):

    db = get_db()


    total = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["count"]


    allowed = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND decision = 'ALLOW'
        """,
        (user_id,)
    ).fetchone()["count"]


    alerts = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND decision = 'ALERT'
        """,
        (user_id,)
    ).fetchone()["count"]


    blocked = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND decision = 'BLOCK'
        """,
        (user_id,)
    ).fetchone()["count"]


    db.close()


    return {

        "success": True,

        "statistics": {

            "total_transactions":
                total,

            "allowed":
                allowed,

            "alerts":
                alerts,

            "blocked":
                blocked

        }

    }


# =========================================================
# USER PROFILE API
# =========================================================

@app.get("/api/user/{user_id}")
def user_profile(
    user_id: str
):

    user = get_user(
        user_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {

        "success": True,

        "user":
            dict(user)

    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {

        "status": "online",

        "service":
            "SecureFlow-AI",

        "database":
            "SQLite"

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

        "docs":
            "/docs"

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
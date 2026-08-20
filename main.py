from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import random

# =========================================================
# SECUREFLOW-AI BACKEND
# =========================================================

app = FastAPI(
    title="SecureFlow-AI",
    description="AI based real-time UPI fraud detection prototype",
    version="1.0"
)

# Allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "secureflow.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():

    db = get_db()

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
# REQUEST MODEL
# =========================================================

class Transaction(BaseModel):

    user_id: str

    amount: float

    device: str

    location: str

    beneficiary: str

    transaction_time: str

    recent_transactions: int = 0


# =========================================================
# USER PROFILE
# =========================================================

USER_PROFILE = {

    "USER001": {

        "name": "Demo User",

        # Normal transaction behaviour
        "average_amount": 1200,

        # Known device
        "device": "Android-Primary",

        # Normal location
        "location": "Kolkata",

        # Frequently used beneficiary
        "beneficiary": "rahul@upi"
    }
}


# =========================================================
# BEHAVIOURAL ANALYSIS
# =========================================================

def analyze_behaviour(transaction, profile):

    score = 0

    reasons = []

    # -----------------------------------------------------
    # 1. AMOUNT ANALYSIS
    # -----------------------------------------------------

    average = profile["average_amount"]

    amount_ratio = transaction.amount / average

    if amount_ratio >= 10:

        score += 30

        reasons.append(
            "Transaction amount is extremely high compared with normal behaviour."
        )

    elif amount_ratio >= 5:

        score += 25

        reasons.append(
            "Transaction amount is significantly higher than normal."
        )

    elif amount_ratio >= 3:

        score += 18

        reasons.append(
            "Transaction amount is higher than normal."
        )

    elif amount_ratio >= 2:

        score += 10

        reasons.append(
            "Transaction amount is moderately higher than normal."
        )


    # -----------------------------------------------------
    # 2. DEVICE ANALYSIS
    # -----------------------------------------------------

    if transaction.device != profile["device"]:

        score += 20

        reasons.append(
            "New or unknown device detected."
        )


    # -----------------------------------------------------
    # 3. LOCATION ANALYSIS
    # -----------------------------------------------------

    if transaction.location != profile["location"]:

        score += 15

        reasons.append(
            "Transaction originates from a new location."
        )


    # -----------------------------------------------------
    # 4. BENEFICIARY ANALYSIS
    # -----------------------------------------------------

    if transaction.beneficiary != profile["beneficiary"]:

        score += 15

        reasons.append(
            "New beneficiary detected."
        )


    # -----------------------------------------------------
    # 5. TIME ANALYSIS
    # -----------------------------------------------------

    try:

        time = datetime.strptime(
            transaction.transaction_time,
            "%I:%M %p"
        )

        hour = time.hour

        if hour >= 23 or hour < 5:

            score += 15

            reasons.append(
                "Transaction occurs during unusual hours."
            )

    except ValueError:

        pass


    # -----------------------------------------------------
    # 6. TRANSACTION FREQUENCY
    # -----------------------------------------------------

    if transaction.recent_transactions >= 8:

        score += 15

        reasons.append(
            "Very high transaction frequency detected."
        )

    elif transaction.recent_transactions >= 5:

        score += 8

        reasons.append(
            "Transaction frequency is higher than normal."
        )


    return min(score, 100), reasons


# =========================================================
# SIMPLE ML-LIKE RISK CALCULATION
# =========================================================

def calculate_ai_score(
    transaction,
    behaviour_score
):

    """
    Prototype AI scoring layer.

    In the final production version this can be replaced
    with a trained Scikit-learn/XGBoost model.
    """

    ai_score = behaviour_score

    # Add small uncertainty factor
    ai_score += random.uniform(
        -3,
        3
    )

    return round(
        max(
            0,
            min(
                ai_score,
                100
            )
        ),
        2
    )


# =========================================================
# DECISION ENGINE
# =========================================================

def make_decision(score):

    # Project risk bands:
    #
    # 0 - 30    = ALLOW
    # 31 - 70   = ALERT
    # 71 - 100  = BLOCK

    if score <= 30:

        return "LOW", "ALLOW"

    elif score <= 70:

        return "MEDIUM", "ALERT"

    else:

        return "HIGH", "BLOCK"


# =========================================================
# DYNAMIC VERIFICATION
# =========================================================

def generate_verification(
    transaction,
    profile
):

    questions = []

    if transaction.device != profile["device"]:

        questions.append(
            "Are you currently using a new device?"
        )

    if transaction.location != profile["location"]:

        questions.append(
            "Are you currently making this payment from a new location?"
        )

    if transaction.beneficiary != profile["beneficiary"]:

        questions.append(
            "Did you intentionally make a payment to this new beneficiary?"
        )

    if transaction.amount > (
        profile["average_amount"] * 3
    ):

        questions.append(
            "Did you personally initiate this high-value transaction?"
        )

    if not questions:

        questions.append(
            "Did you personally initiate this transaction?"
        )

    return random.choice(questions)


# =========================================================
# ANALYZE TRANSACTION API
# =========================================================

@app.post("/api/analyze")
def analyze_transaction(
    transaction: Transaction
):

    # Check user
    profile = USER_PROFILE.get(
        transaction.user_id
    )

    if not profile:

        return {
            "success": False,
            "message": "User not found"
        }


    # Behaviour analysis
    behaviour_score, reasons = (
        analyze_behaviour(
            transaction,
            profile
        )
    )


    # AI score
    ai_score = calculate_ai_score(
        transaction,
        behaviour_score
    )


    # Final score
    final_score = ai_score


    # Decision
    risk_level, decision = (
        make_decision(
            final_score
        )
    )


    # Verification question
    verification_question = None

    if decision == "ALERT":

        verification_question = (
            generate_verification(
                transaction,
                profile
            )
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
            risk_level,
            decision,
            reasons,
            created_at
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,

        (
            transaction.user_id,
            transaction.amount,
            transaction.device,
            transaction.location,
            transaction.beneficiary,
            transaction.transaction_time,
            final_score,
            risk_level,
            decision,
            " | ".join(reasons),
            datetime.now().isoformat()
        )
    )

    transaction_id = cursor.lastrowid

    db.commit()
    db.close()


    # Response
    return {

        "success": True,

        "transaction_id":
            transaction_id,

        "risk": {

            "score":
                final_score,

            "level":
                risk_level
        },

        "decision":
            decision,

        "reasons":
            reasons,

        "verification":
            verification_question
    }


# =========================================================
# TRANSACTION HISTORY
# =========================================================

@app.get("/api/transactions/{user_id}")
def get_transactions(
    user_id: str
):

    db = get_db()

    transactions = db.execute(
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
            dict(transaction)
            for transaction in transactions
        ]
    }


# =========================================================
# USER PROFILE API
# =========================================================

@app.get("/api/user/{user_id}")
def get_user(
    user_id: str
):

    profile = USER_PROFILE.get(
        user_id
    )

    if not profile:

        return {
            "success": False,
            "message": "User not found"
        }

    return {

        "success": True,

        "user_id":
            user_id,

        "profile":
            profile
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/api/health")
def health():

    return {

        "success": True,

        "status": "ONLINE",

        "service":
            "SecureFlow-AI",

        "message":
            "Fraud detection backend is running"
    }


# =========================================================
# SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
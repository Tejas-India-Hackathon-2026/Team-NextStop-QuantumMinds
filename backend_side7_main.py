# ============================================================
# SECUREFLOW-AI — COMPLETE BACKEND
# ============================================================
#
# FastAPI backend compatible with the existing SecureFlow-AI
# frontend.
#
# RISK ENGINE:
#
# 1. Time anomaly              = 7
# 2. Transaction frequency     = 12
# 3. New device                = 15
# 4. Unusual location          = 15
# 5. Sudden location change    = 6
# 6. Unknown beneficiary      = 12
# 7. Previous transaction     = 13
# 8. Typical amount            = 10
#
# These 8 signals = 90 points.
#
# Amount anomaly is NOT a checkbox.
# Amount anomaly = maximum 10 additional points.
#
# TOTAL = maximum 100
#
# 0–49   -> SUCCESS
# 50–79  -> HOLD + DYNAMIC QUESTION
# 80–100 -> BLOCK
#
# Dynamic questions are taken ONLY from the screenshots supplied
# by the user.
#
# 36 records:
# 9 question types × 4 users
#
# U001 = Soumadip Das
# U002 = Shubham Paul
# U003 = Shubham Mukherjee
# U004 = Tridip Debroy
#
# Balance is DISPLAYED and checked.
# Balance is NOT deducted, as requested.
#
# ============================================================


from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
import uuid
import random
import re
import os
from datetime import datetime
from typing import Any, Dict


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="SecureFlow-AI",
    version="3.0.0",
    description="Behavioural UPI fraud detection system"
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "secureflow.db"
)


def db():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# FOUR PAYERS
# ============================================================

USERS = {
    "U001": {
        "name": "Soumadip Das",
        "balance": 55000.0
    },

    "U002": {
        "name": "Shubham Paul",
        "balance": 60000.0
    },

    "U003": {
        "name": "Shubham Mukherjee",
        "balance": 50000.0
    },

    "U004": {
        "name": "Tridip Debroy",
        "balance": 40000.0
    }
}


# ============================================================
# QUESTION BANK
#
# EXACTLY BASED ON THE PROVIDED SCREENSHOTS
# ============================================================

QUESTIONS = {

    "U001": [
        {
            "id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2005-04-18"
        },
        {
            "id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },
        {
            "id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },
        {
            "id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near ...",
            "factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Railway Station"
        },
        {
            "id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "factor": "Known device",
            "answer_type": "TEXT",
            "answer": "Samsung Galaxy S23 - SOUMADIP"
        },
        {
            "id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },
        {
            "id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        }
    ],

    "U002": [
        {
            "id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2004-11-07"
        },
        {
            "id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },
        {
            "id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },
        {
            "id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near ...",
            "factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Township"
        },
        {
            "id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "factor": "Known device",
            "answer_type": "TEXT",
            "answer": "OnePlus 12R - SHUBHAM"
        },
        {
            "id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Kolkata"
        },
        {
            "id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        }
    ],

    "U003": [
        {
            "id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2005-02-21"
        },
        {
            "id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },
        {
            "id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },
        {
            "id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near ...",
            "factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Dock Complex"
        },
        {
            "id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "factor": "Known device",
            "answer_type": "TEXT",
            "answer": "Redmi Note 13 Pro - MUKHERJEE"
        },
        {
            "id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },
        {
            "id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        }
    ],

    "U004": [
        {
            "id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2004-08-13"
        },
        {
            "id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },
        {
            "id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },
        {
            "id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near ...",
            "factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Township"
        },
        {
            "id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "factor": "Known device",
            "answer_type": "TEXT",
            "answer": "Google Pixel 8 - TRIDIP"
        },
        {
            "id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Kolkata"
        },
        {
            "id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },
        {
            "id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        }
    ]
}


# ============================================================
# EXACT 8 CHECKBOX WEIGHTS
# ============================================================

RISK_WEIGHTS = {
    "time_anomaly": 7,
    "transaction_frequency": 12,
    "new_device": 15,
    "unusual_location": 15,
    "sudden_location_change": 6,
    "unknown_beneficiary": 12,
    "previous_transaction": 13,
    "typical_amount": 10
}


# ============================================================
# IN-MEMORY VERIFICATION CHALLENGES
# ============================================================

CHALLENGES: Dict[str, Dict[str, Any]] = {}


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = db()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            balance REAL NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            payer_id TEXT NOT NULL,
            payer_name TEXT NOT NULL,
            recipient_name TEXT NOT NULL,
            recipient_upi_id TEXT NOT NULL,
            amount REAL NOT NULL,
            risk_score INTEGER,
            amount_risk_score INTEGER,
            signal_score INTEGER,
            decision TEXT NOT NULL,
            status TEXT NOT NULL,
            challenge_id TEXT,
            question_code TEXT,
            verification_status TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    for user_id, user in USERS.items():

        cursor.execute(
            """
            INSERT OR IGNORE INTO users
            (
                user_id,
                name,
                balance,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                user["name"],
                user["balance"],
                datetime.now().isoformat()
            )
        )

    connection.commit()
    connection.close()


initialize_database()


# ============================================================
# NORMALIZE ANSWERS
# ============================================================

def normalize(value: Any) -> str:

    if value is None:
        return ""

    value = str(value).strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


# ============================================================
# ANSWER CHECK
# ============================================================

def answer_is_correct(
    supplied: str,
    expected: str
) -> bool:

    supplied = normalize(supplied)
    expected = normalize(expected)

    if supplied == expected:
        return True

    yes = {
        "yes",
        "y",
        "true"
    }

    no = {
        "no",
        "n",
        "false"
    }

    if supplied in yes and expected in yes:
        return True

    if supplied in no and expected in no:
        return True

    return False


# ============================================================
# USER LOOKUP
# ============================================================

def get_user(
    user_id: str
):

    connection = db()

    row = connection.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    return row


# ============================================================
# PREVIOUS TRANSACTION CHECK
# ============================================================

def recipient_has_history(
    payer_id: str,
    recipient_upi_id: str
) -> bool:

    connection = db()

    row = connection.execute(
        """
        SELECT transaction_id
        FROM transactions
        WHERE payer_id = ?
        AND lower(recipient_upi_id) = lower(?)
        AND status = 'SUCCESS'
        LIMIT 1
        """,
        (
            payer_id,
            recipient_upi_id
        )
    ).fetchone()

    connection.close()

    return row is not None


# ============================================================
# SUCCESSFUL AMOUNT HISTORY
# ============================================================

def get_previous_amounts(
    payer_id: str
):

    connection = db()

    rows = connection.execute(
        """
        SELECT amount
        FROM transactions
        WHERE payer_id = ?
        AND status = 'SUCCESS'
        ORDER BY created_at ASC
        """,
        (payer_id,)
    ).fetchall()

    connection.close()

    return [
        float(row["amount"])
        for row in rows
    ]


# ============================================================
# AMOUNT RISK
#
# IMPORTANT:
#
# amount <= 1000:
#       0 points
#
# amount > 1000:
#       compare against THIS payer's own history.
#
# This is NOT one of the 8 checkboxes.
# ============================================================

def calculate_amount_risk(
    payer_id: str,
    amount: float
) -> int:

    if amount <= 1000:
        return 0

    history = get_previous_amounts(
        payer_id
    )

    if len(history) == 0:
        return 5

    average = sum(history) / len(history)

    if average <= 0:
        return 5

    deviation = abs(
        amount - average
    ) / average

    if deviation < 0.50:
        return 0

    if deviation < 1.00:
        return 3

    if deviation < 2.00:
        return 6

    return 10


# ============================================================
# RISK ENGINE
# ============================================================

def calculate_risk(
    payer_id: str,
    amount: float,
    payload: Dict[str, Any]
):

    # --------------------------------------------------------
    # EXACTLY 8 CHECKBOX SIGNALS
    # --------------------------------------------------------

    signals = {
        "time_anomaly": bool(
            payload.get(
                "time_anomaly",
                False
            )
        ),

        "transaction_frequency": bool(
            payload.get(
                "transaction_frequency",
                False
            )
        ),

        "new_device": bool(
            payload.get(
                "new_device",
                False
            )
        ),

        "unusual_location": bool(
            payload.get(
                "unusual_location",
                False
            )
        ),

        "sudden_location_change": bool(
            payload.get(
                "sudden_location_change",
                False
            )
        ),

        "unknown_beneficiary": bool(
            payload.get(
                "unknown_beneficiary",
                False
            )
        ),

        "previous_transaction": bool(
            payload.get(
                "previous_transaction",
                False
            )
        ),

        "typical_amount": bool(
            payload.get(
                "typical_amount",
                False
            )
        )
    }

    signal_score = 0

    triggered = []

    for name, active in signals.items():

        if active:

            signal_score += RISK_WEIGHTS[name]

            triggered.append(name)

    # --------------------------------------------------------
    # AUTOMATIC RECIPIENT HISTORY
    # --------------------------------------------------------

    recipient_upi_id = str(
        payload.get(
            "recipient_upi_id",
            ""
        )
    ).strip()

    if recipient_upi_id:

        known = recipient_has_history(
            payer_id,
            recipient_upi_id
        )

    else:

        known = False

    # If recipient has actually been used before,
    # don't punish it as unknown.

    if known:

        if signals["unknown_beneficiary"]:

            signal_score -= RISK_WEIGHTS[
                "unknown_beneficiary"
            ]

            if "unknown_beneficiary" in triggered:

                triggered.remove(
                    "unknown_beneficiary"
                )

    # If it is genuinely new, add the unknown recipient
    # risk automatically.

    else:

        if not signals["unknown_beneficiary"]:

            signal_score += RISK_WEIGHTS[
                "unknown_beneficiary"
            ]

            triggered.append(
                "unknown_beneficiary"
            )

    # --------------------------------------------------------
    # AMOUNT MODEL
    # --------------------------------------------------------

    amount_score = calculate_amount_risk(
        payer_id,
        amount
    )

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    total = signal_score + amount_score

    total = max(
        0,
        min(
            100,
            total
        )
    )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    if total >= 80:

        decision = "BLOCK"

    elif total >= 50:

        decision = "HOLD"

    else:

        decision = "ALLOW"

    return {
        "risk_score": int(total),
        "signal_score": int(signal_score),
        "amount_risk_score": int(amount_score),
        "decision": decision,
        "triggered_signals": triggered,
        "recipient_known": known
    }


# ============================================================
# DYNAMIC QUESTION SELECTION
#
# The question is selected according to the risk-causing
# behaviour where possible.
#
# For example:
#
# new_device -> DEVICE_CONFIRM
# unusual_location -> LOCATION_CONFIRM
# unknown_beneficiary -> RECIPIENT_CONFIRM
# previous_transaction -> HISTORY_CONFIRM
#
# Otherwise a random question belonging to THAT payer
# is selected.
# ============================================================

SIGNAL_TO_QUESTION = {
    "new_device": "DEVICE_CONFIRM",
    "unusual_location": "LOCATION_CONFIRM",
    "sudden_location_change": "LOCATION_CONFIRM",
    "unknown_beneficiary": "RECIPIENT_CONFIRM",
    "previous_transaction": "HISTORY_CONFIRM",
    "typical_amount": "AMOUNT_CONFIRM",
    "time_anomaly": "HISTORY_CONFIRM",
    "transaction_frequency": "HISTORY_CONFIRM"
}


def create_dynamic_question(
    payer_id: str,
    risk_result: Dict[str, Any],
    transaction_id: str
):

    # --------------------------------------------------------
    # IMPORTANT:
    # Questions are generated ONLY when risk = 50–79.
    # --------------------------------------------------------

    if not (
        50 <= risk_result["risk_score"] <= 79
    ):
        return None

    payer_questions = QUESTIONS.get(
        payer_id
    )

    if not payer_questions:

        raise HTTPException(
            status_code=500,
            detail="No question data exists for this payer."
        )

    triggered = risk_result[
        "triggered_signals"
    ]

    selected_code = None

    # --------------------------------------------------------
    # Prefer a question related to the actual risk.
    # --------------------------------------------------------

    for signal in triggered:

        possible_code = SIGNAL_TO_QUESTION.get(
            signal
        )

        if possible_code:

            matching = [
                q
                for q in payer_questions
                if q["code"] == possible_code
            ]

            if matching:

                selected_code = possible_code
                break

    # --------------------------------------------------------
    # If no direct mapping exists, randomly select one.
    # --------------------------------------------------------

    if selected_code is None:

        selected = random.choice(
            payer_questions
        )

    else:

        selected = next(
            q
            for q in payer_questions
            if q["code"] == selected_code
        )

    # --------------------------------------------------------
    # Create unique challenge.
    # --------------------------------------------------------

    challenge_id = str(
        uuid.uuid4()
    )

    challenge = {
        "challenge_id": challenge_id,
        "transaction_id": transaction_id,
        "payer_id": payer_id,
        "question_id": selected["id"],
        "question_code": selected["code"],
        "question": selected["question"],
        "factor": selected["factor"],
        "answer_type": selected["answer_type"],
        "expected_answer": selected["answer"],
        "attempts": 0,
        "created_at": datetime.now().isoformat()
    }

    CHALLENGES[
        challenge_id
    ] = challenge

    # --------------------------------------------------------
    # NEVER send expected_answer to frontend.
    # --------------------------------------------------------

    return {
        "challenge_id": challenge_id,
        "question_id": selected["id"],
        "question_code": selected["code"],
        "question": selected["question"],
        "factor": selected["factor"],
        "answer_type": selected["answer_type"]
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "ok",
        "service": "SecureFlow-AI",
        "dynamic_questions": True,
        "question_source": "supplied screenshots",
        "question_count": 36,
        "users": 4
    }


# ============================================================
# USERS
# ============================================================

@app.get("/users")
def get_users():

    connection = db()

    rows = connection.execute(
        """
        SELECT
            user_id,
            name,
            balance
        FROM users
        ORDER BY user_id
        """
    ).fetchall()

    connection.close()

    return {
        "users": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get("/transactions/{payer_id}")
def get_transactions(
    payer_id: str
):

    user = get_user(
        payer_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="Payer not found."
        )

    connection = db()

    rows = connection.execute(
        """
        SELECT
            transaction_id,
            payer_id,
            payer_name,
            recipient_name,
            recipient_upi_id,
            amount,
            risk_score,
            amount_risk_score,
            signal_score,
            decision,
            status,
            question_code,
            verification_status,
            created_at
        FROM transactions
        WHERE payer_id = ?
        ORDER BY created_at DESC
        """,
        (payer_id,)
    ).fetchall()

    connection.close()

    return {
        "transactions": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# ANALYZE + PAY
#
# Supports:
#
# POST /analyze-payment
#
# and
#
# POST /analyze
#
# so the existing frontend can use either.
# ============================================================

async def analyze_payment_logic(
    request: Request
):

    try:
        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON request."
        )

    # --------------------------------------------------------
    # Accept common frontend naming variations.
    # --------------------------------------------------------

    payer_id = (
        payload.get("payer_id")
        or payload.get("payerId")
        or payload.get("user_id")
        or payload.get("userId")
    )

    recipient_name = (
        payload.get("recipient_name")
        or payload.get("recipientName")
        or payload.get("upi_name")
        or payload.get("upiName")
        or ""
    )

    recipient_upi_id = (
        payload.get("recipient_upi_id")
        or payload.get("recipientUpiId")
        or payload.get("upi_id")
        or payload.get("upiId")
        or ""
    )

    amount_value = (
        payload.get("amount")
        or payload.get("transaction_amount")
        or payload.get("transactionAmount")
    )

    if not payer_id:

        raise HTTPException(
            status_code=400,
            detail="payer_id is required."
        )

    if amount_value is None:

        raise HTTPException(
            status_code=400,
            detail="amount is required."
        )

    try:

        amount = float(
            amount_value
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Amount must be numeric."
        )

    if amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Amount must be greater than zero."
        )

    payer_id = str(
        payer_id
    ).strip()

    recipient_name = str(
        recipient_name
    ).strip()

    recipient_upi_id = str(
        recipient_upi_id
    ).strip()

    # --------------------------------------------------------
    # Validate payer.
    # --------------------------------------------------------

    user = get_user(
        payer_id
    )

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="Payer not found."
        )

    balance = float(
        user["balance"]
    )

    # --------------------------------------------------------
    # INSUFFICIENT BALANCE
    #
    # No risk analysis is performed.
    # --------------------------------------------------------

    if amount > balance:

        transaction_id = str(
            uuid.uuid4()
        )

        now = datetime.now().isoformat()

        connection = db()

        connection.execute(
            """
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                payer_name,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                amount_risk_score,
                signal_score,
                decision,
                status,
                challenge_id,
                question_code,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                payer_id,
                user["name"],
                recipient_name,
                recipient_upi_id,
                amount,
                None,
                None,
                None,
                "INSUFFICIENT_BALANCE",
                "INSUFFICIENT_BALANCE",
                None,
                None,
                "NOT_REQUIRED",
                now
            )
        )

        connection.commit()
        connection.close()

        return {
            "status": "INSUFFICIENT_BALANCE",
            "decision": "INSUFFICIENT_BALANCE",
            "message": "Insufficient balance.",
            "risk_score": None,
            "transaction_id": transaction_id,
            "payer": user["name"],
            "balance": balance
        }

    # --------------------------------------------------------
    # RISK ANALYSIS
    # --------------------------------------------------------

    risk = calculate_risk(
        payer_id,
        amount,
        payload
    )

    risk_score = risk[
        "risk_score"
    ]

    decision = risk[
        "decision"
    ]

    transaction_id = str(
        uuid.uuid4()
    )

    now = datetime.now().isoformat()

    # ========================================================
    # HIGH RISK — BLOCK
    # ========================================================

    if decision == "BLOCK":

        connection = db()

        connection.execute(
            """
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                payer_name,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                amount_risk_score,
                signal_score,
                decision,
                status,
                challenge_id,
                question_code,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                payer_id,
                user["name"],
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                risk["amount_risk_score"],
                risk["signal_score"],
                "BLOCK",
                "BLOCKED",
                None,
                None,
                "NOT_REQUIRED",
                now
            )
        )

        connection.commit()
        connection.close()

        return {
            "status": "BLOCKED",
            "decision": "BLOCK",
            "message": "Transaction blocked — insecure transaction.",
            "risk_score": risk_score,
            "amount_risk_score": risk[
                "amount_risk_score"
            ],
            "signal_score": risk[
                "signal_score"
            ],
            "triggered_signals": risk[
                "triggered_signals"
            ],
            "transaction_id": transaction_id,
            "payer": user["name"],
            "balance": balance
        }

    # ========================================================
    # MEDIUM RISK — HOLD + DYNAMIC QUESTION
    # ========================================================

    if decision == "HOLD":

        # ----------------------------------------------------
        # THIS IS WHERE THE DYNAMIC QUESTION IS CREATED.
        # ----------------------------------------------------

        challenge = create_dynamic_question(
            payer_id,
            risk,
            transaction_id
        )

        connection = db()

        connection.execute(
            """
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                payer_name,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                amount_risk_score,
                signal_score,
                decision,
                status,
                challenge_id,
                question_code,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                payer_id,
                user["name"],
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                risk["amount_risk_score"],
                risk["signal_score"],
                "HOLD",
                "HELD",
                challenge["challenge_id"],
                challenge["question_code"],
                "PENDING",
                now
            )
        )

        connection.commit()
        connection.close()

        return {
            "status": "HELD",
            "decision": "HOLD",
            "message": "Transaction temporarily held for verification.",
            "risk_score": risk_score,
            "amount_risk_score": risk[
                "amount_risk_score"
            ],
            "signal_score": risk[
                "signal_score"
            ],
            "triggered_signals": risk[
                "triggered_signals"
            ],
            "transaction_id": transaction_id,
            "payer": user["name"],
            "balance": balance,

            # Frontend reads this.
            "challenge": challenge,

            # Also provide these names for compatibility
            # with different frontend implementations.
            "question": challenge["question"],
            "question_code": challenge[
                "question_code"
            ],
            "challenge_id": challenge[
                "challenge_id"
            ]
        }

    # ========================================================
    # LOW RISK — SUCCESS
    # ========================================================

    connection = db()

    connection.execute(
        """
        INSERT INTO transactions
        (
            transaction_id,
            payer_id,
            payer_name,
            recipient_name,
            recipient_upi_id,
            amount,
            risk_score,
            amount_risk_score,
            signal_score,
            decision,
            status,
            challenge_id,
            question_code,
            verification_status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            payer_id,
            user["name"],
            recipient_name,
            recipient_upi_id,
            amount,
            risk_score,
            risk["amount_risk_score"],
            risk["signal_score"],
            "ALLOW",
            "SUCCESS",
            None,
            None,
            "NOT_REQUIRED",
            now
        )
    )

    connection.commit()
    connection.close()

    return {
        "status": "SUCCESS",
        "decision": "ALLOW",
        "message": "Payment successful.",
        "risk_score": risk_score,
        "amount_risk_score": risk[
            "amount_risk_score"
        ],
        "signal_score": risk[
            "signal_score"
        ],
        "triggered_signals": risk[
            "triggered_signals"
        ],
        "transaction_id": transaction_id,
        "payer": user["name"],
        "balance": balance
    }


@app.post("/analyze-payment")
async def analyze_payment(
    request: Request
):

    return await analyze_payment_logic(
        request
    )


@app.post("/analyze")
async def analyze_alias(
    request: Request
):

    return await analyze_payment_logic(
        request
    )


# ============================================================
# VERIFY DYNAMIC QUESTION
#
# CORRECT ANSWER:
#     HELD -> SUCCESS
#
# WRONG ANSWER:
#     HELD -> FAILED/BLOCKED
# ============================================================

async def verify_logic(
    request: Request
):

    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON request."
        )

    challenge_id = (
        payload.get("challenge_id")
        or payload.get("challengeId")
    )

    answer = (
        payload.get("answer")
        or payload.get("user_answer")
        or payload.get("userAnswer")
        or ""
    )

    if not challenge_id:

        raise HTTPException(
            status_code=400,
            detail="challenge_id is required."
        )

    challenge = CHALLENGES.get(
        challenge_id
    )

    if challenge is None:

        raise HTTPException(
            status_code=404,
            detail="Verification challenge not found or expired."
        )

    challenge["attempts"] += 1

    transaction_id = challenge[
        "transaction_id"
    ]

    # --------------------------------------------------------
    # MAXIMUM 3 ATTEMPTS
    # --------------------------------------------------------

    if challenge["attempts"] > 3:

        connection = db()

        connection.execute(
            """
            UPDATE transactions
            SET
                status = 'FAILED',
                decision = 'BLOCK',
                verification_status = 'FAILED'
            WHERE transaction_id = ?
            """,
            (transaction_id,)
        )

        connection.commit()
        connection.close()

        CHALLENGES.pop(
            challenge_id,
            None
        )

        return {
            "status": "FAILED",
            "decision": "BLOCK",
            "message": "Maximum verification attempts exceeded. Payment blocked.",
            "transaction_id": transaction_id
        }

    # --------------------------------------------------------
    # CHECK ANSWER AGAINST SCREENSHOT DATA
    # --------------------------------------------------------

    correct = answer_is_correct(
        str(answer),
        challenge["expected_answer"]
    )

    # ========================================================
    # WRONG
    # ========================================================

    if not correct:

        connection = db()

        connection.execute(
            """
            UPDATE transactions
            SET
                status = 'FAILED',
                decision = 'BLOCK',
                verification_status = 'FAILED'
            WHERE transaction_id = ?
            """,
            (transaction_id,)
        )

        connection.commit()
        connection.close()

        connection_challenge = CHALLENGES.pop(
            challenge_id,
            None
        )

        connection = db()

        row = connection.execute(
            """
            SELECT risk_score
            FROM transactions
            WHERE transaction_id = ?
            """,
            (transaction_id,)
        ).fetchone()

        connection.close()

        score = (
            row["risk_score"]
            if row
            else None
        )

        return {
            "status": "FAILED",
            "decision": "BLOCK",
            "message": "Incorrect answer. Payment blocked.",
            "risk_score": score,
            "transaction_id": transaction_id
        }

    # ========================================================
    # CORRECT
    #
    # THIS RELEASES THE PAYMENT.
    # ========================================================

    connection = db()

    transaction = connection.execute(
        """
        SELECT *
        FROM transactions
        WHERE transaction_id = ?
        """,
        (transaction_id,)
    ).fetchone()

    if transaction is None:

        connection.close()

        CHALLENGES.pop(
            challenge_id,
            None
        )

        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    # --------------------------------------------------------
    # Only HELD transactions can be released.
    # --------------------------------------------------------

    if transaction["status"] != "HELD":

        connection.close()

        CHALLENGES.pop(
            challenge_id,
            None
        )

        return {
            "status": "FAILED",
            "decision": "BLOCK",
            "message": "This transaction is no longer awaiting verification.",
            "risk_score": transaction[
                "risk_score"
            ],
            "transaction_id": transaction_id
        }

    # --------------------------------------------------------
    # RELEASE HELD PAYMENT.
    # --------------------------------------------------------

    connection.execute(
        """
        UPDATE transactions
        SET
            status = 'SUCCESS',
            decision = 'ALLOW',
            verification_status = 'PASSED'
        WHERE transaction_id = ?
        """,
        (transaction_id,)
    )

    connection.commit()
    connection.close()

    CHALLENGES.pop(
        challenge_id,
        None
    )

    # --------------------------------------------------------
    # GET BALANCE
    # --------------------------------------------------------

    user = get_user(
        transaction["payer_id"]
    )

    return {
        "status": "SUCCESS",
        "decision": "ALLOW",
        "message": "Correct answer. Payment successful.",
        "risk_score": transaction[
            "risk_score"
        ],
        "transaction_id": transaction_id,
        "payer": transaction[
            "payer_name"
        ],
        "balance": float(
            user["balance"]
        )
    }


@app.post("/verify-challenge")
async def verify_challenge(
    request: Request
):

    return await verify_logic(
        request
    )


@app.post("/verify")
async def verify_alias(
    request: Request
):

    return await verify_logic(
        request
    )


# ============================================================
# GET QUESTION BANK
#
# Answers are NEVER returned.
#
# Useful for testing the frontend.
# ============================================================

@app.get("/questions/{payer_id}")
def get_questions(
    payer_id: str
):

    if payer_id not in QUESTIONS:

        raise HTTPException(
            status_code=404,
            detail="Question bank not found."
        )

    return {
        "payer_id": payer_id,
        "questions": [
            {
                "id": q["id"],
                "code": q["code"],
                "question": q["question"],
                "factor": q["factor"],
                "answer_type": q["answer_type"]
            }
            for q in QUESTIONS[payer_id]
        ]
    }


# ============================================================
# RESET DASHBOARD
# ============================================================

@app.post("/reset-dashboard")
def reset_dashboard():

    connection = db()

    connection.execute(
        "DELETE FROM transactions"
    )

    # --------------------------------------------------------
    # Restore original displayed balances.
    # --------------------------------------------------------

    for user_id, user in USERS.items():

        connection.execute(
            """
            UPDATE users
            SET balance = ?
            WHERE user_id = ?
            """,
            (
                user["balance"],
                user_id
            )
        )

    connection.commit()
    connection.close()

    # --------------------------------------------------------
    # Delete all active verification challenges.
    # --------------------------------------------------------

    CHALLENGES.clear()

    return {
        "status": "SUCCESS",
        "message": "Dashboard reset successfully.",
        "users": [
            {
                "user_id": user_id,
                "name": user["name"],
                "balance": user["balance"]
            }
            for user_id, user in USERS.items()
        ]
    }


# ============================================================
# CURRENT CHALLENGES — DEBUG/DEMO
#
# Does NOT expose answers.
# ============================================================

@app.get("/active-challenges")
def active_challenges():

    return {
        "count": len(CHALLENGES),
        "challenges": [
            {
                "challenge_id": value[
                    "challenge_id"
                ],
                "transaction_id": value[
                    "transaction_id"
                ],
                "payer_id": value[
                    "payer_id"
                ],
                "question_code": value[
                    "question_code"
                ],
                "attempts": value[
                    "attempts"
                ]
            }
            for value in CHALLENGES.values()
        ]
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "service": "SecureFlow-AI",
        "status": "running",
        "risk_engine": {
            "low": "0-49",
            "hold": "50-79",
            "block": "80-100"
        },
        "dynamic_questions": True,
        "question_source": "provided screenshots",
        "users": 4,
        "question_records": 36
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print()
    print("=" * 70)
    print("                    SECUREFLOW-AI")
    print("=" * 70)
    print()
    print("Backend running at:")
    print("http://127.0.0.1:8000")
    print()
    print("API documentation:")
    print("http://127.0.0.1:8000/docs")
    print()
    print("Dynamic questions: ENABLED")
    print("Question source: PROVIDED SCREENSHOTS")
    print("Question records: 36")
    print()
    print("Risk ranges:")
    print("0 - 49    -> PAYMENT SUCCESS")
    print("50 - 79   -> HOLD + DYNAMIC QUESTION")
    print("80 - 100  -> PAYMENT BLOCKED")
    print()
    print("Payers:")
    print("U001 -> Soumadip Das       -> Rs. 55,000")
    print("U002 -> Shubham Paul        -> Rs. 60,000")
    print("U003 -> Shubham Mukherjee   -> Rs. 50,000")
    print("U004 -> Tridip Debroy       -> Rs. 40,000")
    print()
    print("=" * 70)
    print()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
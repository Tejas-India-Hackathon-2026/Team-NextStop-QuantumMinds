# ============================================================
# SECUREFLOW-AI BACKEND
# ============================================================
# Copy-paste this entire file as:
#
#     backend.py
#
# Install:
#     pip install fastapi uvicorn
#
# Run:
#     python backend.py
#
# API:
#     http://127.0.0.1:8000
#     http://127.0.0.1:8000/docs
#
# ============================================================

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
import uuid
import random
import os
import re
from datetime import datetime
from typing import Any, Dict


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="SecureFlow-AI",
    version="4.0",
    description="Behavioural UPI Risk Analysis Backend"
)

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
DB_PATH = os.path.join(BASE_DIR, "secureflow.db")


def get_db():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# PAYERS
# ============================================================

PAYERS = {

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
# QUESTION DATABASE
#
# These values are taken from the supplied screenshots.
#
# 9 QUESTION TYPES × 4 PAYERS = 36 RECORDS
#
# Expected answers are NEVER returned to the frontend.
# ============================================================

QUESTION_BANK = {

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
# RISK ENGINE
#
# THE USER'S PROVIDED RISK SCORES
#
# Amount                  10
# Time                     7
# Frequency               12
# New Device              15
# Unusual Location        15
# Sudden Location Change   6
# Unknown Beneficiary     12
# Previous Transaction    13
# Typical Amount          10
#
# We deliberately do NOT create a checkbox for Amount.
#
# Therefore the frontend has exactly 8 switches:
#
# 1 Time anomaly
# 2 Frequency anomaly
# 3 New device
# 4 Unusual location
# 5 Sudden location change
# 6 Unknown beneficiary
# 7 Previous transaction anomaly
# 8 Typical amount anomaly
#
# Amount deviation is calculated automatically by the backend.
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


# Maximum automatic amount-deviation contribution.
AMOUNT_DEVIATION_MAX = 10


# ============================================================
# ACTIVE VERIFICATION CHALLENGES
# ============================================================

CHALLENGES = {}


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def initialize_database():

    connection = get_db()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            user_id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            balance REAL NOT NULL,

            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (

            transaction_id TEXT PRIMARY KEY,

            payer_id TEXT NOT NULL,

            payer_name TEXT NOT NULL,

            recipient_name TEXT,

            recipient_upi_id TEXT,

            amount REAL NOT NULL,

            risk_score INTEGER,

            signal_score INTEGER,

            amount_risk_score INTEGER,

            decision TEXT NOT NULL,

            status TEXT NOT NULL,

            challenge_id TEXT,

            question_code TEXT,

            verification_status TEXT,

            created_at TEXT NOT NULL
        )
    """)

    for user_id, payer in PAYERS.items():

        cursor.execute("""
            INSERT OR IGNORE INTO users
            (
                user_id,
                name,
                balance,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (
            user_id,
            payer["name"],
            payer["balance"],
            datetime.now().isoformat()
        ))

    connection.commit()
    connection.close()


initialize_database()


# ============================================================
# UTILITY
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


def get_payer(payer_id: str):

    connection = get_db()

    row = connection.execute("""
        SELECT *
        FROM users
        WHERE user_id = ?
    """, (
        payer_id,
    )).fetchone()

    connection.close()

    return row


# ============================================================
# SUPPORT BOTH SNAKE_CASE AND CAMELCASE FRONTEND FIELDS
# ============================================================

def get_field(
    payload: Dict[str, Any],
    *names,
    default=None
):

    for name in names:

        if name in payload:

            return payload[name]

    return default


# ============================================================
# BOOLEAN PARSER
# ============================================================

def as_bool(value: Any) -> bool:

    if isinstance(value, bool):
        return value

    if value is None:
        return False

    if isinstance(value, (int, float)):

        return value != 0

    return normalize(value) in {
        "true",
        "1",
        "yes",
        "y",
        "on",
        "active",
        "enabled"
    }


# ============================================================
# GET USER'S SUCCESSFUL TRANSACTION HISTORY
# ============================================================

def get_successful_amounts(
    payer_id: str
):

    connection = get_db()

    rows = connection.execute("""
        SELECT amount
        FROM transactions
        WHERE payer_id = ?
        AND status = 'SUCCESS'
        ORDER BY created_at ASC
    """, (
        payer_id,
    )).fetchall()

    connection.close()

    return [
        float(row["amount"])
        for row in rows
    ]


# ============================================================
# PREVIOUS PAYMENT CHECK
# ============================================================

def has_previous_payment(
    payer_id: str,
    recipient_upi_id: str
) -> bool:

    if not recipient_upi_id:
        return False

    connection = get_db()

    row = connection.execute("""
        SELECT transaction_id
        FROM transactions
        WHERE payer_id = ?
        AND lower(recipient_upi_id) = lower(?)
        AND status = 'SUCCESS'
        LIMIT 1
    """, (
        payer_id,
        recipient_upi_id
    )).fetchone()

    connection.close()

    return row is not None


# ============================================================
# AUTOMATIC AMOUNT-DEVIATION ENGINE
#
# IMPORTANT:
#
# <= ₹1000:
#     amount anomaly = 0
#
# > ₹1000:
#     backend studies ONLY THIS USER'S successful history.
#
# No fixed amount penalty is used.
# ============================================================

def calculate_amount_deviation(
    payer_id: str,
    amount: float
) -> int:

    # User specifically requested no amount anomaly
    # when amount is <= 1000.

    if amount <= 1000:

        return 0

    history = get_successful_amounts(
        payer_id
    )

    # There is no personal transaction pattern yet.
    # Therefore there is no evidence of deviation.

    if not history:

        return 0

    average = sum(history) / len(history)

    if average <= 0:

        return 0

    # Compare new transaction with the payer's own
    # previous successful transaction pattern.

    deviation = abs(
        amount - average
    ) / average

    if deviation <= 0.25:

        return 0

    if deviation <= 0.50:

        return 2

    if deviation <= 0.75:

        return 4

    if deviation <= 1.00:

        return 6

    if deviation <= 1.50:

        return 8

    return 10


# ============================================================
# RISK CHECKBOX EXTRACTION
#
# EXACTLY 8 SIGNALS.
#
# Multiple frontend naming styles are accepted.
# ============================================================

def read_risk_switches(
    payload: Dict[str, Any]
):

    return {

        "time_anomaly": as_bool(
            get_field(
                payload,
                "time_anomaly",
                "timeAnomaly",
                "time",
                default=False
            )
        ),

        "transaction_frequency": as_bool(
            get_field(
                payload,
                "transaction_frequency",
                "transactionFrequency",
                "frequency",
                default=False
            )
        ),

        "new_device": as_bool(
            get_field(
                payload,
                "new_device",
                "newDevice",
                default=False
            )
        ),

        "unusual_location": as_bool(
            get_field(
                payload,
                "unusual_location",
                "unusualLocation",
                default=False
            )
        ),

        "sudden_location_change": as_bool(
            get_field(
                payload,
                "sudden_location_change",
                "suddenLocationChange",
                default=False
            )
        ),

        "unknown_beneficiary": as_bool(
            get_field(
                payload,
                "unknown_beneficiary",
                "unknownBeneficiary",
                default=False
            )
        ),

        "previous_transaction": as_bool(
            get_field(
                payload,
                "previous_transaction",
                "previousTransaction",
                default=False
            )
        ),

        "typical_amount": as_bool(
            get_field(
                payload,
                "typical_amount",
                "typicalAmount",
                default=False
            )
        )
    }


# ============================================================
# RISK ENGINE
# ============================================================

def calculate_risk(
    payer_id: str,
    amount: float,
    payload: Dict[str, Any]
):

    switches = read_risk_switches(
        payload
    )

    signal_score = 0

    triggered_signals = []

    # --------------------------------------------------------
    # EXACT 8 CHECKBOXES
    # --------------------------------------------------------

    for signal, enabled in switches.items():

        if enabled:

            weight = RISK_WEIGHTS[
                signal
            ]

            signal_score += weight

            triggered_signals.append(
                signal
            )

    # --------------------------------------------------------
    # AMOUNT DEVIATION
    #
    # NOT A CHECKBOX.
    # Automatically calculated.
    # --------------------------------------------------------

    amount_risk = calculate_amount_deviation(
        payer_id,
        amount
    )

    # --------------------------------------------------------
    # TOTAL SCORE
    # --------------------------------------------------------

    total_score = (
        signal_score +
        amount_risk
    )

    total_score = max(
        0,
        min(
            100,
            total_score
        )
    )

    # --------------------------------------------------------
    # USER'S REQUESTED FINAL DECISION RANGES
    #
    # 0–49  = ALLOW
    # 50–79 = HOLD + QUESTION
    # 80+   = BLOCK
    # --------------------------------------------------------

    if total_score >= 80:

        decision = "BLOCK"

    elif total_score >= 50:

        decision = "HOLD"

    else:

        decision = "ALLOW"

    return {

        "risk_score": int(total_score),

        "signal_score": int(signal_score),

        "amount_risk_score": int(
            amount_risk
        ),

        "decision": decision,

        "triggered_signals":
            triggered_signals,

        "switches":
            switches
    }


# ============================================================
# QUESTION MAPPING
#
# Risk signal -> question from supplied table
# ============================================================

SIGNAL_QUESTION_MAP = {

    "new_device":
        "DEVICE_CONFIRM",

    "unusual_location":
        "LOCATION_CONFIRM",

    "sudden_location_change":
        "LOCATION_CONFIRM",

    "unknown_beneficiary":
        "RECIPIENT_CONFIRM",

    "previous_transaction":
        "HISTORY_CONFIRM",

    "typical_amount":
        "AMOUNT_CONFIRM",

    "time_anomaly":
        "HISTORY_CONFIRM",

    "transaction_frequency":
        "HISTORY_CONFIRM"
}


# ============================================================
# CREATE DYNAMIC QUESTION
#
# ONLY called for risk 50–79.
#
# The actual question and expected answer come from the
# supplied 36-row table.
# ============================================================

def create_dynamic_question(
    payer_id: str,
    risk_result: Dict[str, Any],
    transaction_id: str
):

    risk_score = risk_result[
        "risk_score"
    ]

    # Absolutely no question for low/high risk.

    if not (
        50 <= risk_score <= 79
    ):

        return None

    questions = QUESTION_BANK.get(
        payer_id
    )

    if not questions:

        raise HTTPException(
            status_code=500,
            detail="Question data missing for this payer."
        )

    triggered = risk_result[
        "triggered_signals"
    ]

    selected = None

    # --------------------------------------------------------
    # First try to ask a question related to the actual
    # suspicious behaviour.
    # --------------------------------------------------------

    for signal in triggered:

        question_code = SIGNAL_QUESTION_MAP.get(
            signal
        )

        if not question_code:
            continue

        matching = [
            q for q in questions
            if q["code"] == question_code
        ]

        if matching:

            selected = random.choice(
                matching
            )

            break

    # --------------------------------------------------------
    # If there isn't a direct signal match,
    # select from the payer's own question set.
    # --------------------------------------------------------

    if selected is None:

        selected = random.choice(
            questions
        )

    challenge_id = str(
        uuid.uuid4()
    )

    CHALLENGES[
        challenge_id
    ] = {

        "challenge_id":
            challenge_id,

        "transaction_id":
            transaction_id,

        "payer_id":
            payer_id,

        "question_id":
            selected["id"],

        "question_code":
            selected["code"],

        "question":
            selected["question"],

        "factor":
            selected["factor"],

        "answer_type":
            selected["answer_type"],

        "expected_answer":
            selected["answer"],

        "attempts":
            0,

        "created_at":
            datetime.now().isoformat()
    }

    # --------------------------------------------------------
    # NEVER SEND expected_answer.
    # --------------------------------------------------------

    return {

        "challenge_id":
            challenge_id,

        "question_id":
            selected["id"],

        "question_code":
            selected["code"],

        "question":
            selected["question"],

        "factor":
            selected["factor"],

        "answer_type":
            selected["answer_type"]
    }


# ============================================================
# ANSWER NORMALIZATION
# ============================================================

def answer_matches(
    supplied: Any,
    expected: Any
) -> bool:

    supplied = normalize(
        supplied
    )

    expected = normalize(
        expected
    )

    if supplied == expected:

        return True

    yes_values = {
        "yes",
        "y",
        "true",
        "1"
    }

    no_values = {
        "no",
        "n",
        "false",
        "0"
    }

    if (
        supplied in yes_values
        and
        expected in yes_values
    ):

        return True

    if (
        supplied in no_values
        and
        expected in no_values
    ):

        return True

    return False


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status": "online",

        "service":
            "SecureFlow-AI",

        "dynamic_questions":
            True,

        "question_records":
            36,

        "payers":
            4,

        "risk_engine":
            "enabled"
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "service":
            "SecureFlow-AI",

        "status":
            "running",

        "risk_ranges": {

            "low":
                "0-49",

            "medium":
                "50-79",

            "high":
                "80-100"
        },

        "dynamic_questions":
            True,

        "question_source":
            "Provided table images",

        "checkbox_count":
            8
    }


# ============================================================
# GET PAYERS
# ============================================================

@app.get("/users")
@app.get("/payers")
def get_payers():

    connection = get_db()

    rows = connection.execute("""
        SELECT
            user_id,
            name,
            balance
        FROM users
        ORDER BY user_id
    """).fetchall()

    connection.close()

    return {

        "payers": [
            dict(row)
            for row in rows
        ],

        "users": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# GET SINGLE PAYER
# ============================================================

@app.get("/users/{payer_id}")
def get_single_payer(
    payer_id: str
):

    payer = get_payer(
        payer_id
    )

    if payer is None:

        raise HTTPException(
            status_code=404,
            detail="Payer not found."
        )

    return {

        "user_id":
            payer["user_id"],

        "name":
            payer["name"],

        "balance":
            float(payer["balance"])
    }


# ============================================================
# ANALYZE + PAY
#
# Compatible endpoints:
#
# POST /analyze-payment
# POST /analyze
# POST /analyze-and-pay
# POST /pay
#
# Risk score is generated ONLY here.
# ============================================================

async def process_payment(
    request: Request
):

    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON body."
        )

    # --------------------------------------------------------
    # PAYER
    # --------------------------------------------------------

    payer_id = get_field(
        payload,
        "payer_id",
        "payerId",
        "user_id",
        "userId"
    )

    if payer_id is None:

        raise HTTPException(
            status_code=400,
            detail="payer_id is required."
        )

    payer_id = str(
        payer_id
    ).strip()

    payer = get_payer(
        payer_id
    )

    if payer is None:

        raise HTTPException(
            status_code=404,
            detail="Payer does not exist."
        )

    # --------------------------------------------------------
    # RECIPIENT
    #
    # Recipient can be ANY name / UPI ID.
    # --------------------------------------------------------

    recipient_name = get_field(
        payload,
        "recipient_name",
        "recipientName",
        "upi_name",
        "upiName",
        default=""
    )

    recipient_upi_id = get_field(
        payload,
        "recipient_upi_id",
        "recipientUpiId",
        "upi_id",
        "upiId",
        default=""
    )

    recipient_name = str(
        recipient_name
    ).strip()

    recipient_upi_id = str(
        recipient_upi_id
    ).strip()

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    amount_value = get_field(
        payload,
        "amount",
        "transaction_amount",
        "transactionAmount"
    )

    if amount_value is None:

        raise HTTPException(
            status_code=400,
            detail="Transaction amount is required."
        )

    try:

        amount = float(
            amount_value
        )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Transaction amount must be numeric."
        )

    if amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Transaction amount must be greater than zero."
        )

    # --------------------------------------------------------
    # CHECK BALANCE BEFORE RISK ENGINE
    # --------------------------------------------------------

    balance = float(
        payer["balance"]
    )

    transaction_id = str(
        uuid.uuid4()
    )

    now = datetime.now().isoformat()

    if amount > balance:

        connection = get_db()

        connection.execute("""
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                payer_name,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                signal_score,
                amount_risk_score,
                decision,
                status,
                challenge_id,
                question_code,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            transaction_id,

            payer_id,

            payer["name"],

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
        ))

        connection.commit()
        connection.close()

        return {

            "status":
                "INSUFFICIENT_BALANCE",

            "decision":
                "INSUFFICIENT_BALANCE",

            "message":
                "Insufficient balance.",

            "transaction_id":
                transaction_id,

            "payer":
                payer["name"],

            "balance":
                balance,

            "amount":
                amount,

            "risk_score":
                None
        }

    # ========================================================
    # RUN RISK ENGINE
    # ========================================================

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

    # ========================================================
    # HIGH RISK — 80+
    #
    # BLOCK IMMEDIATELY.
    # ========================================================

    if risk_score >= 80:

        connection = get_db()

        connection.execute("""
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                payer_name,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                signal_score,
                amount_risk_score,
                decision,
                status,
                challenge_id,
                question_code,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            transaction_id,

            payer_id,

            payer["name"],

            recipient_name,

            recipient_upi_id,

            amount,

            risk_score,

            risk["signal_score"],

            risk["amount_risk_score"],

            "BLOCK",

            "BLOCKED",

            None,

            None,

            "NOT_REQUIRED",

            now
        ))

        connection.commit()
        connection.close()

        return {

            "status":
                "BLOCKED",

            "decision":
                "BLOCK",

            "message":
                "Insecure transaction blocked.",

            "transaction_id":
                transaction_id,

            "payer":
                payer["name"],

            "balance":
                balance,

            "amount":
                amount,

            "risk_score":
                risk_score,

            "signal_score":
                risk["signal_score"],

            "amount_risk_score":
                risk["amount_risk_score"],

            "triggered_signals":
                risk["triggered_signals"],

            "switches":
                risk["switches"],

            "challenge":
                None
        }

    # ========================================================
    # MEDIUM RISK — 50 TO 79
    #
    # HOLD + DYNAMIC QUESTION.
    # ========================================================

    if 50 <= risk_score <= 79:

        challenge = create_dynamic_question(
            payer_id,
            risk,
            transaction_id
        )

        if challenge is None:

            raise HTTPException(
                status_code=500,
                detail="Unable to create dynamic verification question."
            )

        connection = get_db()

        connection.execute("""
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                payer_name,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                signal_score,
                amount_risk_score,
                decision,
                status,
                challenge_id,
                question_code,
                verification_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (

            transaction_id,

            payer_id,

            payer["name"],

            recipient_name,

            recipient_upi_id,

            amount,

            risk_score,

            risk["signal_score"],

            risk["amount_risk_score"],

            "HOLD",

            "HELD",

            challenge["challenge_id"],

            challenge["question_code"],

            "PENDING",

            now
        ))

        connection.commit()
        connection.close()

        return {

            "status":
                "HELD",

            "decision":
                "HOLD",

            "message":
                "Transaction temporarily held. Identity verification required.",

            "transaction_id":
                transaction_id,

            "payer":
                payer["name"],

            "balance":
                balance,

            "amount":
                amount,

            "risk_score":
                risk_score,

            "signal_score":
                risk["signal_score"],

            "amount_risk_score":
                risk["amount_risk_score"],

            "triggered_signals":
                risk["triggered_signals"],

            "switches":
                risk["switches"],

            "challenge":
                challenge,

            # Compatibility fields for existing frontend
            "challenge_id":
                challenge["challenge_id"],

            "question":
                challenge["question"],

            "question_code":
                challenge["question_code"],

            "answer_type":
                challenge["answer_type"],

            "verification_required":
                True
        }

    # ========================================================
    # LOW RISK — 0 TO 49
    #
    # PAYMENT SUCCESSFUL.
    # ========================================================

    connection = get_db()

    connection.execute("""
        INSERT INTO transactions
        (
            transaction_id,
            payer_id,
            payer_name,
            recipient_name,
            recipient_upi_id,
            amount,
            risk_score,
            signal_score,
            amount_risk_score,
            decision,
            status,
            challenge_id,
            question_code,
            verification_status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        transaction_id,

        payer_id,

        payer["name"],

        recipient_name,

        recipient_upi_id,

        amount,

        risk_score,

        risk["signal_score"],

        risk["amount_risk_score"],

        "ALLOW",

        "SUCCESS",

        None,

        None,

        "NOT_REQUIRED",

        now
    ))

    connection.commit()
    connection.close()

    return {

        "status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "message":
            "Payment successful.",

        "transaction_id":
            transaction_id,

        "payer":
            payer["name"],

        "balance":
            balance,

        "amount":
            amount,

        "risk_score":
            risk_score,

        "signal_score":
            risk["signal_score"],

        "amount_risk_score":
            risk["amount_risk_score"],

        "triggered_signals":
            risk["triggered_signals"],

        "switches":
            risk["switches"],

        "challenge":
            None
    }


@app.post("/analyze-payment")
async def analyze_payment(
    request: Request
):

    return await process_payment(
        request
    )


@app.post("/analyze")
async def analyze(
    request: Request
):

    return await process_payment(
        request
    )


@app.post("/analyze-and-pay")
async def analyze_and_pay(
    request: Request
):

    return await process_payment(
        request
    )


@app.post("/pay")
async def pay(
    request: Request
):

    return await process_payment(
        request
    )


# ============================================================
# VERIFY DYNAMIC QUESTION
#
# CORRECT:
#     HELD -> SUCCESS
#
# WRONG:
#     HELD -> FAILED / BLOCKED
#
# BALANCE IS NOT DEDUCTED.
# ============================================================

async def process_verification(
    request: Request
):

    try:

        payload = await request.json()

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON body."
        )

    challenge_id = get_field(
        payload,
        "challenge_id",
        "challengeId"
    )

    answer = get_field(
        payload,
        "answer",
        "user_answer",
        "userAnswer",
        default=""
    )

    if not challenge_id:

        raise HTTPException(
            status_code=400,
            detail="challenge_id is required."
        )

    challenge = CHALLENGES.get(
        str(challenge_id)
    )

    if challenge is None:

        raise HTTPException(
            status_code=404,
            detail="Verification challenge not found or expired."
        )

    # --------------------------------------------------------
    # Maximum 3 attempts.
    # --------------------------------------------------------

    challenge["attempts"] += 1

    transaction_id = challenge[
        "transaction_id"
    ]

    # --------------------------------------------------------
    # CHECK TRANSACTION
    # --------------------------------------------------------

    connection = get_db()

    transaction = connection.execute("""
        SELECT *
        FROM transactions
        WHERE transaction_id = ?
    """, (
        transaction_id,
    )).fetchone()

    connection.close()

    if transaction is None:

        CHALLENGES.pop(
            str(challenge_id),
            None
        )

        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    if transaction["status"] != "HELD":

        CHALLENGES.pop(
            str(challenge_id),
            None
        )

        return {

            "status":
                "FAILED",

            "decision":
                "BLOCK",

            "message":
                "This transaction is no longer awaiting verification.",

            "transaction_id":
                transaction_id,

            "risk_score":
                transaction["risk_score"]
        }

    # ========================================================
    # MAXIMUM ATTEMPTS
    # ========================================================

    if challenge["attempts"] > 3:

        connection = get_db()

        connection.execute("""
            UPDATE transactions

            SET
                status = 'FAILED',
                decision = 'BLOCK',
                verification_status = 'FAILED'

            WHERE transaction_id = ?
        """, (
            transaction_id,
        ))

        connection.commit()
        connection.close()

        CHALLENGES.pop(
            str(challenge_id),
            None
        )

        return {

            "status":
                "FAILED",

            "decision":
                "BLOCK",

            "message":
                "Maximum verification attempts exceeded. Payment blocked.",

            "transaction_id":
                transaction_id,

            "risk_score":
                transaction["risk_score"]
        }

    # ========================================================
    # ANSWER CHECK
    # ========================================================

    correct = answer_matches(
        answer,
        challenge["expected_answer"]
    )

    # ========================================================
    # WRONG ANSWER
    # ========================================================

    if not correct:

        connection = get_db()

        connection.execute("""
            UPDATE transactions

            SET
                status = 'FAILED',
                decision = 'BLOCK',
                verification_status = 'FAILED'

            WHERE transaction_id = ?
        """, (
            transaction_id,
        ))

        connection.commit()
        connection.close()

        CHALLENGES.pop(
            str(challenge_id),
            None
        )

        return {

            "status":
                "FAILED",

            "decision":
                "BLOCK",

            "message":
                "Incorrect answer. Payment blocked.",

            "transaction_id":
                transaction_id,

            "risk_score":
                transaction["risk_score"],

            "verification":
                "FAILED"
        }

    # ========================================================
    # CORRECT ANSWER
    #
    # THIS IS THE IMPORTANT FIX:
    #
    # The held transaction is explicitly changed to SUCCESS.
    # ========================================================

    connection = get_db()

    connection.execute("""
        UPDATE transactions

        SET
            status = 'SUCCESS',
            decision = 'ALLOW',
            verification_status = 'PASSED'

        WHERE transaction_id = ?
    """, (
        transaction_id,
    ))

    connection.commit()
    connection.close()

    CHALLENGES.pop(
        str(challenge_id),
        None
    )

    payer = get_payer(
        transaction["payer_id"]
    )

    return {

        "status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "message":
            "Correct answer. Payment successful.",

        "transaction_id":
            transaction_id,

        "payer":
            transaction["payer_name"],

        "recipient_name":
            transaction["recipient_name"],

        "recipient_upi_id":
            transaction["recipient_upi_id"],

        "amount":
            transaction["amount"],

        "risk_score":
            transaction["risk_score"],

        "balance":
            float(payer["balance"]),

        "verification":
            "PASSED",

        "payment_released":
            True
    }


@app.post("/verify")
async def verify(
    request: Request
):

    return await process_verification(
        request
    )


@app.post("/verify-challenge")
async def verify_challenge(
    request: Request
):

    return await process_verification(
        request
    )


@app.post("/answer-question")
async def answer_question(
    request: Request
):

    return await process_verification(
        request
    )


# ============================================================
# GET QUESTION SET
#
# This endpoint is useful for debugging the frontend.
# Answers are intentionally hidden.
# ============================================================

@app.get("/questions/{payer_id}")
def get_questions(
    payer_id: str
):

    if payer_id not in QUESTION_BANK:

        raise HTTPException(
            status_code=404,
            detail="Payer question set not found."
        )

    return {

        "payer_id":
            payer_id,

        "questions": [

            {
                "id":
                    question["id"],

                "code":
                    question["code"],

                "question":
                    question["question"],

                "factor":
                    question["factor"],

                "answer_type":
                    question["answer_type"]
            }

            for question
            in QUESTION_BANK[payer_id]
        ]
    }


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.get("/transactions")
def all_transactions():

    connection = get_db()

    rows = connection.execute("""
        SELECT *
        FROM transactions
        ORDER BY created_at DESC
    """).fetchall()

    connection.close()

    return {

        "transactions":
            [dict(row) for row in rows]
    }


@app.get("/transactions/{payer_id}")
def payer_transactions(
    payer_id: str
):

    payer = get_payer(
        payer_id
    )

    if payer is None:

        raise HTTPException(
            status_code=404,
            detail="Payer not found."
        )

    connection = get_db()

    rows = connection.execute("""
        SELECT *
        FROM transactions
        WHERE payer_id = ?
        ORDER BY created_at DESC
    """, (
        payer_id,
    )).fetchall()

    connection.close()

    return {

        "payer":
            dict(payer),

        "transactions":
            [dict(row) for row in rows]
    }


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@app.get("/dashboard")
def dashboard():

    connection = get_db()

    transaction_count = connection.execute("""
        SELECT COUNT(*)
        FROM transactions
    """).fetchone()[0]

    success_count = connection.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE status = 'SUCCESS'
    """).fetchone()[0]

    blocked_count = connection.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE status = 'BLOCKED'
    """).fetchone()[0]

    held_count = connection.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE status = 'HELD'
    """).fetchone()[0]

    failed_count = connection.execute("""
        SELECT COUNT(*)
        FROM transactions
        WHERE status = 'FAILED'
    """).fetchone()[0]

    connection.close()

    return {

        "transaction_count":
            transaction_count,

        "successful":
            success_count,

        "blocked":
            blocked_count,

        "held":
            held_count,

        "failed":
            failed_count,

        "payers": [
            {
                "user_id":
                    user_id,

                "name":
                    payer["name"],

                "balance":
                    payer["balance"]
            }

            for user_id, payer
            in PAYERS.items()
        ]
    }


# ============================================================
# RESET DASHBOARD
#
# Transactions are deleted.
# Original displayed balances are restored.
# No money is actually deducted by this demo backend.
# ============================================================

@app.post("/reset-dashboard")
@app.post("/reset")
def reset_dashboard():

    connection = get_db()

    connection.execute(
        "DELETE FROM transactions"
    )

    for user_id, payer in PAYERS.items():

        connection.execute("""
            UPDATE users

            SET balance = ?

            WHERE user_id = ?
        """, (
            payer["balance"],
            user_id
        ))

    connection.commit()
    connection.close()

    CHALLENGES.clear()

    return {

        "status":
            "SUCCESS",

        "message":
            "SecureFlow-AI dashboard reset successfully.",

        "payers": [

            {
                "user_id":
                    user_id,

                "name":
                    payer["name"],

                "balance":
                    payer["balance"]
            }

            for user_id, payer
            in PAYERS.items()
        ]
    }


# ============================================================
# ACTIVE VERIFICATION CHALLENGES
#
# Expected answers are NEVER exposed.
# ============================================================

@app.get("/active-challenges")
def active_challenges():

    return {

        "count":
            len(CHALLENGES),

        "challenges": [

            {

                "challenge_id":
                    challenge["challenge_id"],

                "transaction_id":
                    challenge["transaction_id"],

                "payer_id":
                    challenge["payer_id"],

                "question_code":
                    challenge["question_code"],

                "attempts":
                    challenge["attempts"]
            }

            for challenge
            in CHALLENGES.values()
        ]
    }


# ============================================================
# RISK ENGINE INFORMATION
# ============================================================

@app.get("/risk-engine")
def risk_engine():

    return {

        "checkboxes": [

            {
                "key":
                    "time_anomaly",

                "label":
                    "Time anomaly",

                "weight":
                    7
            },

            {
                "key":
                    "transaction_frequency",

                "label":
                    "Transaction frequency",

                "weight":
                    12
            },

            {
                "key":
                    "new_device",

                "label":
                    "New device",

                "weight":
                    15
            },

            {
                "key":
                    "unusual_location",

                "label":
                    "Unusual location",

                "weight":
                    15
            },

            {
                "key":
                    "sudden_location_change",

                "label":
                    "Sudden location change",

                "weight":
                    6
            },

            {
                "key":
                    "unknown_beneficiary",

                "label":
                    "Unknown beneficiary",

                "weight":
                    12
            },

            {
                "key":
                    "previous_transaction",

                "label":
                    "Previous transaction anomaly",

                "weight":
                    13
            },

            {
                "key":
                    "typical_amount",

                "label":
                    "Typical amount anomaly",

                "weight":
                    10
            }
        ],

        "automatic_amount_deviation": {

            "enabled":
                True,

            "checkbox":
                False,

            "max_score":
                10,

            "no_anomaly_at_or_below":
                1000
        },

        "ranges": {

            "allow":
                "0-49",

            "hold":
                "50-79",

            "block":
                "80-100"
        }
    }


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print()
    print("=" * 72)
    print("                    SECUREFLOW-AI")
    print("=" * 72)
    print()
    print("Backend:")
    print("http://127.0.0.1:8000")
    print()
    print("Swagger:")
    print("http://127.0.0.1:8000/docs")
    print()
    print("QUESTION DATABASE")
    print("-----------------")
    print("36 supplied question records")
    print("4 payers × 9 questions")
    print()
    print("RISK ENGINE")
    print("-----------")
    print("0-49   -> SUCCESS")
    print("50-79  -> HOLD + DYNAMIC QUESTION")
    print("80-100 -> BLOCK")
    print()
    print("CHECKBOXES: 8")
    print("Automatic amount deviation: ENABLED")
    print("Amount <= 1000: NO amount anomaly")
    print()
    print("PAYERS")
    print("------")
    print("U001  Soumadip Das       ₹55,000")
    print("U002  Shubham Paul       ₹60,000")
    print("U003  Shubham Mukherjee  ₹50,000")
    print("U004  Tridip Debroy      ₹40,000")
    print()
    print("Balance deduction: DISABLED")
    print("Dynamic verification: ENABLED")
    print()
    print("=" * 72)
    print()

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
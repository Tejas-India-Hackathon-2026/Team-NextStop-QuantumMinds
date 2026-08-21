# ============================================================
# SECUREFLOW-AI BACKEND
# ============================================================
#
# Run:
#
#     pip install fastapi uvicorn pydantic
#
# Then:
#
#     python backend.py
#
# Backend:
#     http://127.0.0.1:8000
#
# API docs:
#     http://127.0.0.1:8000/docs
#
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from statistics import median
import random
import uuid
import math
import os

# ============================================================
# OPTIONAL ML MODEL
# ============================================================

# If you have your trained model saved as:
#
#     risk_model.joblib
#
# the backend will try to load it automatically.
#
# If it is not present, the built-in behavioural risk engine
# is used so that the backend still works.

ML_MODEL = None

try:
    import joblib

    MODEL_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "risk_model.joblib"
    )

    if os.path.exists(MODEL_PATH):
        ML_MODEL = joblib.load(MODEL_PATH)
        print("[SecureFlow-AI] ML model loaded.")

except Exception as exc:
    ML_MODEL = None
    print(
        "[SecureFlow-AI] ML model not loaded. "
        f"Built-in risk engine will be used. Reason: {exc}"
    )


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="SecureFlow-AI Backend",
    description="Behavioural UPI fraud detection backend",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ORIGINAL PAYER ACCOUNTS
# ============================================================

INITIAL_USERS = {

    "U001": {
        "user_id": "U001",
        "name": "Soumadip Das",
        "balance": 55000.0,

        "device": "Samsung Galaxy S23 - SOUMADIP",
        "area": "Haldia",
        "usual_location": "Haldia",
        "dob": "2005-04-18",
        "college": "Haldia Institute of Technology",
        "nearby_place": "Haldia Railway Station",

    },

    "U002": {
        "user_id": "U002",
        "name": "Shubham Paul",
        "balance": 60000.0,

        "device": "OnePlus 12R - SHUBHAM",
        "area": "Haldia",
        "usual_location": "Kolkata",
        "dob": "2004-11-07",
        "college": "Haldia Institute of Technology",
        "nearby_place": "Haldia Township",

    },

    "U003": {
        "user_id": "U003",
        "name": "Shubham Mukherjee",
        "balance": 50000.0,

        "device": "Redmi Note 13 Pro - MUKHERJEE",
        "area": "Haldia",
        "usual_location": "Haldia",
        "dob": "2005-02-21",
        "college": "Haldia Institute of Technology",
        "nearby_place": "Haldia Dock Complex",

    },

    "U004": {
        "user_id": "U004",
        "name": "Tridip Debroy",
        "balance": 40000.0,

        "device": "Google Pixel 8 - TRIDIP",
        "area": "Haldia",
        "usual_location": "Kolkata",
        "dob": "2004-08-13",
        "college": "Haldia Institute of Technology",
        "nearby_place": "Haldia Township",

    }

}


# ============================================================
# 8 RISK SIGNALS
# ============================================================
#
# Amount deviation is deliberately NOT here.
#
# It is calculated separately by the backend and fed into
# the final risk engine.
#
# The weights shown in the supplied handwritten specification:
#
# Time                     = 7
# Frequency                = 12
# New device               = 15
# Unusual location         = 15
# Sudden location change   = 6
# Unknown beneficiary      = 12
# Previous transaction     = 13
# Typical amount           = 10
#
# These eight signals total 90.
# Amount deviation supplies the remaining amount-pattern
# component internally.
# ============================================================

SIGNAL_WEIGHTS = {

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
# IN-MEMORY DATABASE
# ============================================================

users: Dict[str, Dict[str, Any]] = {}
transactions: Dict[str, List[Dict[str, Any]]] = {}
challenges: Dict[str, Dict[str, Any]] = {}


# ============================================================
# QUESTION DATA FROM PROVIDED TABLE
# ============================================================
#
# These are the 9 question categories visible in the supplied
# screenshots:
#
# 1. DOB_CONFIRM
# 2. COLLEGE_CONFIRM
# 3. AREA_CONFIRM
# 4. NEARBY_PLACE_CONFIRM
# 5. DEVICE_CONFIRM
# 6. LOCATION_CONFIRM
# 7. RECIPIENT_CONFIRM
# 8. HISTORY_CONFIRM
# 9. AMOUNT_CONFIRM
#
# ============================================================

QUESTION_DATA = {

    "U001": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "risk_factor": "Known device",
            "answer_type": "TEXT",
            "answer": "Samsung Galaxy S23 - SOUMADIP"
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "risk_factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "risk_factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2005-04-18"
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near your residence.",
            "risk_factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Railway Station"
        },

        {
            "question_id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "risk_factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "risk_factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "risk_factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        }

    ],


    "U002": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "risk_factor": "Known device",
            "answer_type": "TEXT",
            "answer": "OnePlus 12R - SHUBHAM"
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "risk_factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "risk_factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Kolkata"
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2004-11-07"
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near your residence.",
            "risk_factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Township"
        },

        {
            "question_id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "risk_factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "risk_factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "risk_factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        }

    ],


    "U003": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "risk_factor": "Known device",
            "answer_type": "TEXT",
            "answer": "Redmi Note 13 Pro - MUKHERJEE"
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "risk_factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "risk_factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2005-02-21"
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near your residence.",
            "risk_factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Dock Complex"
        },

        {
            "question_id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "risk_factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "risk_factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "risk_factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        }

    ],


    "U004": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for payments?",
            "risk_factor": "Known device",
            "answer_type": "TEXT",
            "answer": "Google Pixel 8 - TRIDIP"
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "risk_factor": "Residential identity",
            "answer_type": "TEXT",
            "answer": "Haldia"
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "risk_factor": "Location familiarity",
            "answer_type": "TEXT",
            "answer": "Kolkata"
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "2004-08-13"
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "risk_factor": "Personal identity",
            "answer_type": "TEXT",
            "answer": "Haldia Institute of Technology"
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near your residence.",
            "risk_factor": "Residential knowledge",
            "answer_type": "TEXT",
            "answer": "Haldia Township"
        },

        {
            "question_id": 9,
            "code": "AMOUNT_CONFIRM",
            "question": "Is the payment amount shown on the screen the amount you intended to send?",
            "risk_factor": "Amount verification",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 8,
            "code": "HISTORY_CONFIRM",
            "question": "Have you previously made a payment to this recipient?",
            "risk_factor": "Transaction history",
            "answer_type": "YES_NO",
            "answer": "YES"
        },

        {
            "question_id": 7,
            "code": "RECIPIENT_CONFIRM",
            "question": "Do you recognize the recipient of this payment?",
            "risk_factor": "Recipient familiarity",
            "answer_type": "YES_NO",
            "answer": "YES"
        }

    ]

}


# ============================================================
# INITIAL TRANSACTION HISTORY
# ============================================================
#
# These historical transactions are important because the
# amount-deviation engine needs actual user-specific history.
#
# The recipient is not restricted to these values.
# New recipients can be entered freely.
# ============================================================

INITIAL_TRANSACTIONS = {

    "U001": [

        {
            "transaction_id": "TX-U001-001",
            "recipient_name": "College Canteen",
            "recipient_upi_id": "canteen@upi",
            "amount": 250.0,
            "status": "SUCCESS",
            "risk_score": 8.0,
            "timestamp": "2026-08-16T10:15:00"
        },

        {
            "transaction_id": "TX-U001-002",
            "recipient_name": "Amit",
            "recipient_upi_id": "amit@upi",
            "amount": 600.0,
            "status": "SUCCESS",
            "risk_score": 12.0,
            "timestamp": "2026-08-17T17:20:00"
        },

        {
            "transaction_id": "TX-U001-003",
            "recipient_name": "Electricity",
            "recipient_upi_id": "electricity@upi",
            "amount": 850.0,
            "status": "SUCCESS",
            "risk_score": 10.0,
            "timestamp": "2026-08-18T12:30:00"
        }

    ],


    "U002": [

        {
            "transaction_id": "TX-U002-001",
            "recipient_name": "Rahul",
            "recipient_upi_id": "rahul@upi",
            "amount": 300.0,
            "status": "SUCCESS",
            "risk_score": 7.0,
            "timestamp": "2026-08-16T11:00:00"
        },

        {
            "transaction_id": "TX-U002-002",
            "recipient_name": "Food",
            "recipient_upi_id": "food@upi",
            "amount": 550.0,
            "status": "SUCCESS",
            "risk_score": 9.0,
            "timestamp": "2026-08-17T19:10:00"
        },

        {
            "transaction_id": "TX-U002-003",
            "recipient_name": "Book Store",
            "recipient_upi_id": "books@upi",
            "amount": 900.0,
            "status": "SUCCESS",
            "risk_score": 11.0,
            "timestamp": "2026-08-18T14:10:00"
        }

    ],


    "U003": [

        {
            "transaction_id": "TX-U003-001",
            "recipient_name": "Canteen",
            "recipient_upi_id": "canteen@upi",
            "amount": 200.0,
            "status": "SUCCESS",
            "risk_score": 6.0,
            "timestamp": "2026-08-16T09:30:00"
        },

        {
            "transaction_id": "TX-U003-002",
            "recipient_name": "Friend",
            "recipient_upi_id": "friend@upi",
            "amount": 500.0,
            "status": "SUCCESS",
            "risk_score": 8.0,
            "timestamp": "2026-08-17T18:00:00"
        },

        {
            "transaction_id": "TX-U003-003",
            "recipient_name": "Internet",
            "recipient_upi_id": "internet@upi",
            "amount": 750.0,
            "status": "SUCCESS",
            "risk_score": 10.0,
            "timestamp": "2026-08-18T13:15:00"
        }

    ],


    "U004": [

        {
            "transaction_id": "TX-U004-001",
            "recipient_name": "Food",
            "recipient_upi_id": "food@upi",
            "amount": 250.0,
            "status": "SUCCESS",
            "risk_score": 7.0,
            "timestamp": "2026-08-16T12:00:00"
        },

        {
            "transaction_id": "TX-U004-002",
            "recipient_name": "Friend",
            "recipient_upi_id": "friend@upi",
            "amount": 450.0,
            "status": "SUCCESS",
            "risk_score": 8.0,
            "timestamp": "2026-08-17T16:45:00"
        },

        {
            "transaction_id": "TX-U004-003",
            "recipient_name": "Shop",
            "recipient_upi_id": "shop@upi",
            "amount": 800.0,
            "status": "SUCCESS",
            "risk_score": 10.0,
            "timestamp": "2026-08-18T15:20:00"
        }

    ]

}


# ============================================================
# RESET DATABASE
# ============================================================

def reset_database():

    global users
    global transactions
    global challenges

    users = {}

    for user_id, data in INITIAL_USERS.items():

        users[user_id] = dict(data)


    transactions = {}

    for user_id, rows in INITIAL_TRANSACTIONS.items():

        transactions[user_id] = [
            dict(row)
            for row in rows
        ]


    challenges = {}


reset_database()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class PaymentRequest(BaseModel):

    payer_id: str

    recipient_name: str = Field(
        min_length=1,
        max_length=200
    )

    recipient_upi_id: str = Field(
        min_length=1,
        max_length=200
    )

    amount: float = Field(
        gt=0
    )


    # --------------------------------------------------------
    # EXACTLY 8 FRONTEND SIGNALS
    # --------------------------------------------------------

    time_anomaly: bool = False

    transaction_frequency: bool = False

    new_device: bool = False

    unusual_location: bool = False

    sudden_location_change: bool = False

    unknown_beneficiary: bool = False

    previous_transaction: bool = False

    typical_amount: bool = False


    # Optional grouped representation from the frontend.
    # This is accepted but does not create additional signals.
    behaviour_signals: Optional[Dict[str, bool]] = None


class ChallengeVerification(BaseModel):

    challenge_id: str

    answer: str


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def clean_text(value: Any) -> str:

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


def normalize_yes_no(value: str) -> str:

    text = clean_text(value)

    if text in {
        "yes",
        "y",
        "yeah",
        "yep",
        "true"
    }:
        return "yes"

    if text in {
        "no",
        "n",
        "nah",
        "false"
    }:
        return "no"

    return text


def money(value: float) -> float:

    return round(
        float(value),
        2
    )


def user_public_data(user: Dict[str, Any]) -> Dict[str, Any]:

    return {

        "user_id": user["user_id"],

        "name": user["name"],

        "balance": money(
            user["balance"]
        ),

        "current_bank_balance": money(
            user["balance"]
        ),

        "available_balance": money(
            user["balance"]
        )

    }


# ============================================================
# TRANSACTION HISTORY HELPERS
# ============================================================

def get_amount_history(
    payer_id: str
) -> List[float]:

    rows = transactions.get(
        payer_id,
        []
    )

    values = []

    for row in rows:

        amount = row.get(
            "amount"
        )

        try:

            amount = float(amount)

            if amount > 0:
                values.append(amount)

        except (
            TypeError,
            ValueError
        ):
            pass

    return values


def recipient_seen_before(
    payer_id: str,
    recipient_name: str,
    recipient_upi_id: str
) -> bool:

    target_name =
        clean_text(recipient_name)

    target_upi =
        clean_text(recipient_upi_id)


    for row in transactions.get(
        payer_id,
        []
    ):

        old_name =
            clean_text(
                row.get(
                    "recipient_name",
                    ""
                )
            )

        old_upi =
            clean_text(
                row.get(
                    "recipient_upi_id",
                    ""
                )
            )


        if target_upi and old_upi == target_upi:
            return True


        if target_name and old_name == target_name:
            return True


    return False


# ============================================================
# AMOUNT-DEVIATION ENGINE
# ============================================================
#
# IMPORTANT:
#
# 1. Amount <= ₹1000:
#       amount risk = 0
#
# 2. Amount > ₹1000:
#       compare against THIS USER'S own transaction history.
#
# No global user's history is used.
#
# The result becomes a feature of the final risk engine.
#
# ============================================================

def calculate_amount_deviation(
    payer_id: str,
    amount: float
) -> Dict[str, float]:

    amount = float(amount)


    # --------------------------------------------------------
    # User requirement:
    # under/equal to 1000 => no amount anomaly
    # --------------------------------------------------------

    if amount <= 1000:

        return {

            "amount_risk": 0.0,

            "amount_baseline": 1000.0,

            "amount_deviation_ratio": 0.0

        }


    history =
        get_amount_history(
            payer_id
        )


    # If history does not exist, use 1000 as conservative
    # baseline rather than inventing a user's behaviour.

    if not history:

        baseline = 1000.0

    else:

        baseline = max(
            100.0,
            float(
                median(history)
            )
        )


    deviation_ratio =
        max(
            0.0,
            (amount - baseline) /
            max(
                baseline,
                1.0
            )
        )


    # Log scaling prevents enormous amounts from producing
    # unlimited risk.

    scaled =
        math.log1p(
            deviation_ratio
        ) / math.log1p(10.0)


    amount_risk =
        min(
            10.0,
            max(
                0.0,
                scaled * 10.0
            )
        )


    return {

        "amount_risk":
            round(
                amount_risk,
                2
            ),

        "amount_baseline":
            round(
                baseline,
                2
            ),

        "amount_deviation_ratio":
            round(
                deviation_ratio,
                4
            )

    }


# ============================================================
# ML FEATURE BUILDER
# ============================================================

def build_model_features(
    request: PaymentRequest,
    amount_info: Dict[str, float],
    payer: Dict[str, Any]
) -> Dict[str, float]:

    return {

        # 8 behavioural signals

        "time_anomaly":
            float(
                request.time_anomaly
            ),

        "transaction_frequency":
            float(
                request.transaction_frequency
            ),

        "new_device":
            float(
                request.new_device
            ),

        "unusual_location":
            float(
                request.unusual_location
            ),

        "sudden_location_change":
            float(
                request.sudden_location_change
            ),

        "unknown_beneficiary":
            float(
                request.unknown_beneficiary
            ),

        "previous_transaction":
            float(
                request.previous_transaction
            ),

        "typical_amount":
            float(
                request.typical_amount
            ),

        # Amount deviation is generated automatically.

        "amount_deviation":
            float(
                amount_info[
                    "amount_risk"
                ]
            ),

        "amount":
            float(
                request.amount
            ),

        "balance":
            float(
                payer["balance"]
            )

    }


# ============================================================
# BUILT-IN BEHAVIOURAL MODEL
# ============================================================
#
# If an actual risk_model.joblib exists, it can be used.
#
# Otherwise this engine combines the paper's eight behavioural
# signals and the automatically generated amount feature.
#
# The final score is ALWAYS normalized to 0-100.
# ============================================================

def built_in_risk_model(
    request: PaymentRequest,
    amount_info: Dict[str, float]
) -> float:

    score = 0.0


    # --------------------------------------------------------
    # Eight paper signals
    # --------------------------------------------------------

    signal_values = {

        "time_anomaly":
            request.time_anomaly,

        "transaction_frequency":
            request.transaction_frequency,

        "new_device":
            request.new_device,

        "unusual_location":
            request.unusual_location,

        "sudden_location_change":
            request.sudden_location_change,

        "unknown_beneficiary":
            request.unknown_beneficiary,

        "previous_transaction":
            request.previous_transaction,

        "typical_amount":
            request.typical_amount

    }


    for signal, active in signal_values.items():

        if active:

            score += SIGNAL_WEIGHTS[
                signal
            ]


    # --------------------------------------------------------
    # Amount deviation
    #
    # Max = 10 points
    #
    # It is NOT a checkbox.
    # --------------------------------------------------------

    score += amount_info[
        "amount_risk"
    ]


    # --------------------------------------------------------
    # Small behavioural interaction bonuses.
    #
    # These represent the AI/behaviour engine noticing that
    # several independent signals occurring together are more
    # suspicious than isolated signals.
    # --------------------------------------------------------

    active_count =
        sum(
            1
            for value in signal_values.values()
            if value
        )


    if active_count >= 3:
        score += 4.0


    if (
        request.new_device
        and request.unusual_location
    ):
        score += 5.0


    if (
        request.unknown_beneficiary
        and request.new_device
    ):
        score += 4.0


    if (
        request.transaction_frequency
        and request.typical_amount
    ):
        score += 3.0


    if (
        request.sudden_location_change
        and request.unusual_location
    ):
        score += 3.0


    return round(
        min(
            100.0,
            max(
                0.0,
                score
            )
        ),
        2
    )


# ============================================================
# OPTIONAL ACTUAL ML MODEL
# ============================================================

def predict_with_ml_model(
    request: PaymentRequest,
    amount_info: Dict[str, float],
    payer: Dict[str, Any]
) -> Optional[float]:

    if ML_MODEL is None:
        return None


    features =
        build_model_features(
            request,
            amount_info,
            payer
        )


    feature_order = [

        "time_anomaly",
        "transaction_frequency",
        "new_device",
        "unusual_location",
        "sudden_location_change",
        "unknown_beneficiary",
        "previous_transaction",
        "typical_amount",
        "amount_deviation",
        "amount",
        "balance"

    ]


    vector = [
        features[name]
        for name in feature_order
    ]


    try:

        # Standard sklearn-style model.

        prediction =
            ML_MODEL.predict(
                [vector]
            )


        value =
            float(
                prediction[0]
            )


        # Some models return 0-1.

        if 0 <= value <= 1:

            value *= 100.0


        return round(
            max(
                0.0,
                min(
                    100.0,
                    value
                )
            ),
            2
        )


    except Exception as exc:

        print(
            "[SecureFlow-AI] ML model prediction "
            f"failed: {exc}"
        )

        return None


# ============================================================
# FINAL RISK SCORE
# ============================================================

def calculate_risk_score(
    request: PaymentRequest,
    payer: Dict[str, Any]
) -> Dict[str, Any]:

    amount_info =
        calculate_amount_deviation(
            request.payer_id,
            request.amount
        )


    ml_score =
        predict_with_ml_model(
            request,
            amount_info,
            payer
        )


    if ml_score is not None:

        final_score =
            ml_score

        model_used =
            "ML model"

    else:

        final_score =
            built_in_risk_model(
                request,
                amount_info
            )

        model_used =
            "SecureFlow behavioural engine"


    # --------------------------------------------------------
    # Thresholds requested by user:
    #
    # 0-49   -> ALLOW
    # 50-79  -> VERIFY
    # 80-100 -> BLOCK
    # --------------------------------------------------------

    if final_score >= 80:

        decision = "BLOCK"

        status = "INSECURE_TRANSACTION"

    elif final_score >= 50:

        decision = "HOLD"

        status = "VERIFICATION_REQUIRED"

    else:

        decision = "ALLOW"

        status = "APPROVED"


    return {

        "risk_score":
            round(
                final_score,
                2
            ),

        "decision":
            decision,

        "status":
            status,

        "model_used":
            model_used,

        "amount_risk":
            amount_info[
                "amount_risk"
            ],

        "amount_baseline":
            amount_info[
                "amount_baseline"
            ],

        "amount_deviation_ratio":
            amount_info[
                "amount_deviation_ratio"
            ]

    }


# ============================================================
# DYNAMIC QUESTION ENGINE
# ============================================================

def choose_dynamic_question(
    payer_id: str,
    request: PaymentRequest,
    amount_info: Dict[str, float]
) -> Dict[str, Any]:

    questions =
        QUESTION_DATA[
            payer_id
        ]


    candidates = []


    # --------------------------------------------------------
    # Strongest relevant questions first.
    # --------------------------------------------------------

    if request.new_device:

        candidates.append(
            "DEVICE_CONFIRM"
        )


    if request.unusual_location:

        candidates.append(
            "LOCATION_CONFIRM"
        )


    if request.sudden_location_change:

        candidates.append(
            "AREA_CONFIRM"
        )


    if request.unknown_beneficiary:

        candidates.append(
            "RECIPIENT_CONFIRM"
        )


    if request.previous_transaction:

        candidates.append(
            "HISTORY_CONFIRM"
        )


    if request.typical_amount:

        candidates.append(
            "AMOUNT_CONFIRM"
        )


    # Automatically generated amount anomaly.

    if (
        amount_info[
            "amount_risk"
        ] > 0
    ):

        candidates.append(
            "AMOUNT_CONFIRM"
        )


    if request.transaction_frequency:

        candidates.append(
            "HISTORY_CONFIRM"
        )


    if request.time_anomaly:

        candidates.append(
            "DOB_CONFIRM"
        )


    # --------------------------------------------------------
    # Remove duplicate codes while retaining order.
    # --------------------------------------------------------

    unique_codes = []

    for code in candidates:

        if code not in unique_codes:

            unique_codes.append(
                code
            )


    # --------------------------------------------------------
    # If there is no specific active signal, use a secure
    # identity question from the payer's own profile.
    # --------------------------------------------------------

    fallback_codes = [

        "RECIPIENT_CONFIRM",
        "HISTORY_CONFIRM",
        "COLLEGE_CONFIRM",
        "AREA_CONFIRM",
        "NEARBY_PLACE_CONFIRM",
        "DOB_CONFIRM"

    ]


    unique_codes.extend(
        code
        for code in fallback_codes
        if code not in unique_codes
    )


    selected_code =
        unique_codes[0]


    matching = [

        question
        for question in questions
        if question["code"] == selected_code
    ]


    if not matching:

        matching = questions


    question =
        random.choice(
            matching
        )


    challenge_id =
        str(
            uuid.uuid4()
        )


    challenges[
        challenge_id
    ] = {

        "challenge_id":
            challenge_id,

        "payer_id":
            payer_id,

        "code":
            question["code"],

        "question":
            question["question"],

        "expected_answer":
            question["answer"],

        "answer_type":
            question["answer_type"],

        "used":
            False,

        "created_at":
            datetime.now().isoformat()

    }


    return {

        "challenge_id":
            challenge_id,

        "question":
            question["question"],

        "question_code":
            question["code"],

        "answer_type":
            question["answer_type"],

        "risk_factor":
            question["risk_factor"]

    }


# ============================================================
# GET USERS
# ============================================================

@app.get("/users")
def get_users():

    return {

        "users": [
            user_public_data(
                users[user_id]
            )
            for user_id in [
                "U001",
                "U002",
                "U003",
                "U004"
            ]
        ]

    }


# ============================================================
# GET ONE USER
# ============================================================

@app.get("/users/{user_id}")
def get_user(
    user_id: str
):

    if user_id not in users:

        raise HTTPException(
            status_code=404,
            detail="Payer account not found."
        )


    return {

        "user":
            user_public_data(
                users[user_id]
            )

    }


# ============================================================
# GET TRANSACTIONS
# ============================================================

@app.get("/transactions/{user_id}")
def get_transactions(
    user_id: str
):

    if user_id not in users:

        raise HTTPException(
            status_code=404,
            detail="Payer account not found."
        )


    rows =
        transactions.get(
            user_id,
            []
        )


    # newest first

    rows =
        list(
            reversed(rows)
        )


    return {

        "transactions":
            rows

    }


# ============================================================
# ANALYZE + PAY
# ============================================================

@app.post("/analyze-payment")
def analyze_payment(
    request: PaymentRequest
):

    payer_id =
        request.payer_id.strip()


    # --------------------------------------------------------
    # PAYER CHECK
    # --------------------------------------------------------

    if payer_id not in users:

        raise HTTPException(
            status_code=404,
            detail="Payer account not found."
        )


    payer =
        users[payer_id]


    # --------------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------------

    recipient_name =
        request.recipient_name.strip()


    recipient_upi =
        request.recipient_upi_id.strip()


    amount =
        float(
            request.amount
        )


    if not recipient_name:

        raise HTTPException(
            status_code=400,
            detail="Recipient name is required."
        )


    if not recipient_upi:

        raise HTTPException(
            status_code=400,
            detail="Recipient UPI ID is required."
        )


    if amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero."
        )


    # --------------------------------------------------------
    # BALANCE CHECK
    #
    # NO deduction happens here.
    #
    # We only reject if amount > available balance.
    # --------------------------------------------------------

    if amount > payer["balance"]:

        return {

            "success": False,

            "status":
                "INSUFFICIENT_BALANCE",

            "decision":
                "INSUFFICIENT_BALANCE",

            "risk_score":
                None,

            "message":
                (
                    f"Insufficient balance. "
                    f"Available balance is "
                    f"₹{payer['balance']:,.2f}."
                ),

            "payer_id":
                payer_id,

            "recipient_name":
                recipient_name,

            "recipient_upi_id":
                recipient_upi,

            "amount":
                amount,

            "available_balance":
                money(
                    payer["balance"]
                )

        }


    # --------------------------------------------------------
    # AUTOMATIC RECIPIENT/HISTORY INFORMATION
    #
    # The backend knows whether the recipient has appeared
    # before, but the frontend still controls the explicit
    # eight behavioural switches.
    # --------------------------------------------------------

    seen_before =
        recipient_seen_before(
            payer_id,
            recipient_name,
            recipient_upi
        )


    # --------------------------------------------------------
    # RISK ANALYSIS
    # --------------------------------------------------------

    risk =
        calculate_risk_score(
            request,
            payer
        )


    score =
        risk[
            "risk_score"
        ]


    # --------------------------------------------------------
    # HIGH RISK: 80+
    #
    # INSECURE TRANSACTION
    # NO money movement.
    # --------------------------------------------------------

    if score >= 80:

        transaction_id =
            "TX-" +
            uuid.uuid4().hex[:12].upper()


        blocked_transaction = {

            "transaction_id":
                transaction_id,

            "recipient_name":
                recipient_name,

            "recipient_upi_id":
                recipient_upi,

            "amount":
                money(amount),

            "status":
                "BLOCKED",

            "transaction_status":
                "BLOCKED",

            "decision":
                "BLOCK",

            "risk_score":
                score,

            "timestamp":
                datetime.now().isoformat(),

            "message":
                "Insecure transaction."

        }


        transactions[
            payer_id
        ].append(
            blocked_transaction
        )


        return {

            "success": False,

            "status":
                "INSECURE_TRANSACTION",

            "decision":
                "BLOCK",

            "risk_score":
                score,

            "model_used":
                risk["model_used"],

            "amount_risk":
                risk["amount_risk"],

            "amount_baseline":
                risk["amount_baseline"],

            "amount_deviation_ratio":
                risk[
                    "amount_deviation_ratio"
                ],

            "recipient_seen_before":
                seen_before,

            "message":
                (
                    "Insecure transaction. "
                    "The risk score is 80 or higher. "
                    "Payment blocked."
                ),

            "payer_id":
                payer_id,

            "recipient_name":
                recipient_name,

            "recipient_upi_id":
                recipient_upi,

            "amount":
                amount,

            "available_balance":
                money(
                    payer["balance"]
                )

        }


    # --------------------------------------------------------
    # MEDIUM RISK: 50-79
    #
    # HOLD.
    #
    # IMPORTANT:
    # No balance deduction.
    # No successful transaction yet.
    # --------------------------------------------------------

    if 50 <= score <= 79:

        challenge =
            choose_dynamic_question(
                payer_id,
                request,
                {
                    "amount_risk":
                        risk["amount_risk"]
                }
            )


        return {

            "success":
                False,

            "status":
                "VERIFICATION_REQUIRED",

            "decision":
                "HOLD",

            "risk_score":
                score,

            "model_used":
                risk["model_used"],

            "amount_risk":
                risk["amount_risk"],

            "amount_baseline":
                risk["amount_baseline"],

            "amount_deviation_ratio":
                risk[
                    "amount_deviation_ratio"
                ],

            "recipient_seen_before":
                seen_before,

            "message":
                (
                    "Payment held for additional "
                    "verification."
                ),

            "payer_id":
                payer_id,

            "recipient_name":
                recipient_name,

            "recipient_upi_id":
                recipient_upi,

            "amount":
                amount,

            "available_balance":
                money(
                    payer["balance"]
                ),

            "challenge":
                challenge

        }


    # --------------------------------------------------------
    # LOW RISK: 0-49
    #
    # PROCEED.
    # --------------------------------------------------------

    transaction_id =
        "TX-" +
        uuid.uuid4().hex[:12].upper()


    payer["balance"] =
        money(
            payer["balance"] -
            amount
        )


    successful_transaction = {

        "transaction_id":
            transaction_id,

        "recipient_name":
            recipient_name,

        "recipient_upi_id":
            recipient_upi,

        "amount":
            money(amount),

        "status":
            "SUCCESS",

        "transaction_status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "risk_score":
            score,

        "timestamp":
            datetime.now().isoformat(),

        "message":
            "Payment successful."

    }


    transactions[
        payer_id
    ].append(
        successful_transaction
    )


    return {

        "success":
            True,

        "status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "risk_score":
            score,

        "model_used":
            risk["model_used"],

        "amount_risk":
            risk["amount_risk"],

        "amount_baseline":
            risk["amount_baseline"],

        "amount_deviation_ratio":
            risk[
                "amount_deviation_ratio"
            ],

        "recipient_seen_before":
            seen_before,

        "message":
            "Payment successful.",

        "payer_id":
            payer_id,

        "recipient_name":
            recipient_name,

        "recipient_upi_id":
            recipient_upi,

        "amount":
            amount,

        "new_balance":
            money(
                payer["balance"]
            ),

        "available_balance":
            money(
                payer["balance"]
            )

    }


# ============================================================
# VERIFY DYNAMIC QUESTION
# ============================================================

@app.post("/verify-challenge")
def verify_challenge(
    verification: ChallengeVerification
):

    challenge_id =
        verification.challenge_id.strip()


    answer =
        verification.answer.strip()


    # --------------------------------------------------------
    # Challenge existence
    # --------------------------------------------------------

    if challenge_id not in challenges:

        raise HTTPException(
            status_code=404,
            detail="Verification challenge not found or expired."
        )


    challenge =
        challenges[
            challenge_id
        ]


    # --------------------------------------------------------
    # Prevent replay
    # --------------------------------------------------------

    if challenge["used"]:

        raise HTTPException(
            status_code=400,
            detail="This verification challenge has already been used."
        )


    payer_id =
        challenge["payer_id"]


    if payer_id not in users:

        raise HTTPException(
            status_code=404,
            detail="Payer account no longer exists."
        )


    payer =
        users[payer_id]


    # --------------------------------------------------------
    # ANSWER VALIDATION
    #
    # Answers come directly from the supplied question table.
    #
    # Text answers are case-insensitive.
    #
    # YES/NO answers are normalized.
    # --------------------------------------------------------

    expected =
        challenge[
            "expected_answer"
        ]


    answer_type =
        challenge[
            "answer_type"
        ]


    if answer_type == "YES_NO":

        supplied =
            normalize_yes_no(
                answer
            )

        expected_normalized =
            normalize_yes_no(
                expected
            )

    else:

        supplied =
            clean_text(
                answer
            )

        expected_normalized =
            clean_text(
                expected
            )


    correct =
        supplied ==
        expected_normalized


    # --------------------------------------------------------
    # Challenge is consumed regardless of answer.
    # --------------------------------------------------------

    challenge["used"] = True


    # --------------------------------------------------------
    # WRONG ANSWER
    # --------------------------------------------------------

    if not correct:

        transaction_id =
            "TX-" +
            uuid.uuid4().hex[:12].upper()


        failed_transaction = {

            "transaction_id":
                transaction_id,

            "recipient_name":
                "Verification failed",

            "recipient_upi_id":
                "",

            "amount":
                0.0,

            "status":
                "BLOCKED",

            "transaction_status":
                "BLOCKED",

            "decision":
                "BLOCK",

            "risk_score":
                None,

            "timestamp":
                datetime.now().isoformat(),

            "message":
                "Dynamic verification failed."

        }


        transactions[
            payer_id
        ].append(
            failed_transaction
        )


        return {

            "success":
                False,

            "correct":
                False,

            "status":
                "FAILED",

            "decision":
                "BLOCK",

            "risk_score":
                None,

            "message":
                (
                    "Payment failed. "
                    "The verification answer was incorrect."
                ),

            "payer_id":
                payer_id,

            "new_balance":
                money(
                    payer["balance"]
                )

        }


    # ========================================================
    # CORRECT ANSWER
    #
    # IMPORTANT:
    #
    # We need the original held transaction information.
    #
    # It is reconstructed from the most recent transaction
    # request stored in the challenge.
    #
    # ========================================================

    held_payment =
        challenge.get(
            "payment"
        )


    if held_payment is None:

        return {

            "success":
                False,

            "correct":
                True,

            "status":
                "FAILED",

            "decision":
                "BLOCK",

            "message":
                (
                    "Verification was correct, "
                    "but the held payment could not be recovered."
                ),

            "payer_id":
                payer_id

        }


    amount =
        float(
            held_payment[
                "amount"
            ]
        )


    recipient_name =
        held_payment[
            "recipient_name"
        ]


    recipient_upi =
        held_payment[
            "recipient_upi_id"
        ]


    # --------------------------------------------------------
    # FINAL BALANCE CHECK
    #
    # This prevents a race-condition style overspend if the
    # balance changed while verification was pending.
    # --------------------------------------------------------

    if amount > payer["balance"]:

        return {

            "success":
                False,

            "correct":
                True,

            "status":
                "INSUFFICIENT_BALANCE",

            "decision":
                "INSUFFICIENT_BALANCE",

            "message":
                (
                    "Verification was correct, "
                    "but the payer no longer has sufficient balance."
                ),

            "payer_id":
                payer_id,

            "new_balance":
                money(
                    payer["balance"]
                )

        }


    # --------------------------------------------------------
    # NOW AND ONLY NOW deduct balance.
    # --------------------------------------------------------

    payer["balance"] =
        money(
            payer["balance"] -
            amount
        )


    transaction_id =
        "TX-" +
        uuid.uuid4().hex[:12].upper()


    successful_transaction = {

        "transaction_id":
            transaction_id,

        "recipient_name":
            recipient_name,

        "recipient_upi_id":
            recipient_upi,

        "amount":
            money(amount),

        "status":
            "SUCCESS",

        "transaction_status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "risk_score":
            held_payment.get(
                "risk_score"
            ),

        "timestamp":
            datetime.now().isoformat(),

        "message":
            "Payment successful after verification."

    }


    transactions[
        payer_id
    ].append(
        successful_transaction
    )


    return {

        "success":
            True,

        "correct":
            True,

        "status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "risk_score":
            held_payment.get(
                "risk_score"
            ),

        "message":
            (
                "Verification successful. "
                "Payment completed."
            ),

        "payer_id":
            payer_id,

        "recipient_name":
            recipient_name,

        "recipient_upi_id":
            recipient_upi,

        "amount":
            amount,

        "new_balance":
            money(
                payer["balance"]
            ),

        "available_balance":
            money(
                payer["balance"]
            )

    }


# ============================================================
# RESET DASHBOARD
# ============================================================

@app.post("/reset-dashboard")
def reset_dashboard():

    reset_database()


    return {

        "success":
            True,

        "message":
            "Dashboard reset successfully.",

        "users":
            [
                user_public_data(
                    users[user_id]
                )
                for user_id in [
                    "U001",
                    "U002",
                    "U003",
                    "U004"
                ]
            ]

    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {

        "status":
            "online",

        "service":
            "SecureFlow-AI",

        "risk_engine":
            (
                "ML model"
                if ML_MODEL is not None
                else "SecureFlow behavioural engine"
            ),

        "payers":
            len(users),

        "timestamp":
            datetime.now().isoformat()

    }


# ============================================================
# DEBUG / QUESTION DATA
# ============================================================
#
# This endpoint is useful during your hackathon demo to show
# that the backend has the four users' dynamic verification
# information.
#
# ============================================================

@app.get("/dynamic-questions/{user_id}")
def get_dynamic_questions(
    user_id: str
):

    if user_id not in QUESTION_DATA:

        raise HTTPException(
            status_code=404,
            detail="Payer not found."
        )


    return {

        "user_id":
            user_id,

        "questions":
            QUESTION_DATA[
                user_id
            ]

    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print()
    print("=" * 60)
    print("        SECUREFLOW-AI BACKEND")
    print("=" * 60)
    print()
    print("Server:  http://127.0.0.1:8000")
    print("Docs:    http://127.0.0.1:8000/docs")
    print()
    print("Payers:")
    print("U001  Soumadip Das       ₹55,000")
    print("U002  Shubham Paul       ₹60,000")
    print("U003  Shubham Mukherjee  ₹50,000")
    print("U004  Tridip Debroy      ₹40,000")
    print()
    print("Risk thresholds:")
    print("0-49   -> ALLOW")
    print("50-79  -> VERIFY")
    print("80-100 -> BLOCK")
    print()
    print("Amount <= ₹1,000 -> no amount anomaly")
    print("Amount > ₹1,000  -> user-history deviation analysis")
    print()
    print("=" * 60)
    print()


    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
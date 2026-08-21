from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from statistics import median
import math
import os
import uuid
import random

# ============================================================
# OPTIONAL ML MODEL
# ============================================================

ML_MODEL = None

try:
    import joblib

    model_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "risk_model.joblib"
    )

    if os.path.exists(model_path):
        ML_MODEL = joblib.load(model_path)
        print("[SecureFlow-AI] ML model loaded.")

except Exception as exc:
    print(f"[SecureFlow-AI] ML model unavailable: {exc}")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="SecureFlow-AI Backend",
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
# FOUR PAYER ACCOUNTS
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
        "nearby_place": "Haldia Railway Station"
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
        "nearby_place": "Haldia Township"
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
        "nearby_place": "Haldia Dock Complex"
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
        "nearby_place": "Haldia Township"
    }
}


# ============================================================
# EXACTLY 8 RISK CHECKBOXES
#
# Amount deviation is NOT a checkbox.
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
# DYNAMIC QUESTIONS FROM PROVIDED TABLE
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
# DATABASE
# ============================================================

users: Dict[str, Dict[str, Any]] = {}
transactions: Dict[str, List[Dict[str, Any]]] = {}
challenges: Dict[str, Dict[str, Any]] = {}


def reset_database() -> None:
    global users
    global transactions
    global challenges

    users = {
        uid: dict(data)
        for uid, data in INITIAL_USERS.items()
    }

    transactions = {
        uid: [dict(row) for row in rows]
        for uid, rows in INITIAL_TRANSACTIONS.items()
    }

    challenges = {}


reset_database()


# ============================================================
# REQUEST MODELS
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

    # EXACTLY 8 SWITCHES

    time_anomaly: bool = False

    transaction_frequency: bool = False

    new_device: bool = False

    unusual_location: bool = False

    sudden_location_change: bool = False

    unknown_beneficiary: bool = False

    previous_transaction: bool = False

    typical_amount: bool = False

    behaviour_signals: Optional[Dict[str, bool]] = None


class ChallengeVerification(BaseModel):

    challenge_id: str

    answer: str


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value: Any) -> str:

    return " ".join(
        str(value or "").strip().lower().split()
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


def public_user(
    user: Dict[str, Any]
) -> Dict[str, Any]:

    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "balance": money(
            user["balance"]
        )
    }


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def amount_history(
    payer_id: str
) -> List[float]:

    values = []

    for row in transactions.get(
        payer_id,
        []
    ):

        if row.get("status") != "SUCCESS":
            continue

        try:

            value = float(
                row.get(
                    "amount",
                    0
                )
            )

            if value > 0:
                values.append(value)

        except (
            TypeError,
            ValueError
        ):
            continue

    return values


def recipient_seen_before(
    payer_id: str,
    recipient_name: str,
    recipient_upi_id: str
) -> bool:

    target_name = clean_text(
        recipient_name
    )

    target_upi = clean_text(
        recipient_upi_id
    )

    for row in transactions.get(
        payer_id,
        []
    ):

        if row.get("status") != "SUCCESS":
            continue

        old_name = clean_text(
            row.get(
                "recipient_name",
                ""
            )
        )

        old_upi = clean_text(
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
# AUTOMATIC AMOUNT DEVIATION
# ============================================================

def calculate_amount_deviation(
    payer_id: str,
    amount: float
) -> Dict[str, float]:

    # ₹1000 or below = NO amount anomaly.

    if amount <= 1000:

        return {
            "amount_risk": 0.0,
            "amount_baseline": 1000.0,
            "amount_deviation_ratio": 0.0
        }

    history = amount_history(
        payer_id
    )

    if history:

        baseline = max(
            100.0,
            float(
                median(history)
            )
        )

    else:

        baseline = 1000.0

    deviation_ratio = max(
        0.0,
        (
            amount - baseline
        ) / max(
            baseline,
            1.0
        )
    )

    scaled = (
        math.log1p(
            deviation_ratio
        )
        /
        math.log1p(10.0)
    )

    amount_risk = min(
        10.0,
        max(
            0.0,
            scaled * 10.0
        )
    )

    return {
        "amount_risk": round(
            amount_risk,
            2
        ),
        "amount_baseline": round(
            baseline,
            2
        ),
        "amount_deviation_ratio": round(
            deviation_ratio,
            4
        )
    }


# ============================================================
# READ THE 8 SWITCHES
# ============================================================

def merge_signal_inputs(
    request: PaymentRequest
) -> Dict[str, bool]:

    values = {
        name: bool(
            getattr(
                request,
                name
            )
        )
        for name in SIGNAL_WEIGHTS
    }

    if request.behaviour_signals:

        unknown = (
            set(
                request.behaviour_signals
            )
            -
            set(
                SIGNAL_WEIGHTS
            )
        )

        if unknown:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Unknown behaviour signal(s): "
                    +
                    ", ".join(
                        sorted(unknown)
                    )
                )
            )

        for name, value in (
            request.behaviour_signals.items()
        ):

            values[name] = bool(
                value
            )

    return values


# ============================================================
# BUILT-IN RISK ENGINE
# ============================================================

def built_in_risk_model(
    signals: Dict[str, bool],
    amount_info: Dict[str, float]
) -> float:

    score = sum(
        SIGNAL_WEIGHTS[name]
        for name, active in signals.items()
        if active
    )

    # Automatic amount-deviation component.
    score += amount_info[
        "amount_risk"
    ]

    active_count = sum(
        1
        for active in signals.values()
        if active
    )

    # Combined behavioural anomalies.

    if active_count >= 3:
        score += 4.0

    if (
        signals["new_device"]
        and
        signals["unusual_location"]
    ):
        score += 5.0

    if (
        signals["unknown_beneficiary"]
        and
        signals["new_device"]
    ):
        score += 4.0

    if (
        signals["transaction_frequency"]
        and
        signals["typical_amount"]
    ):
        score += 3.0

    if (
        signals["sudden_location_change"]
        and
        signals["unusual_location"]
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
# OPTIONAL REAL ML MODEL
# ============================================================

def ml_predict(
    request: PaymentRequest,
    payer: Dict[str, Any],
    signals: Dict[str, bool],
    amount_info: Dict[str, float]
) -> Optional[float]:

    if ML_MODEL is None:
        return None

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

    features = []

    for name in feature_order:

        if name in signals:

            features.append(
                float(
                    signals[name]
                )
            )

        elif name == "amount_deviation":

            features.append(
                float(
                    amount_info[
                        "amount_risk"
                    ]
                )
            )

        elif name == "amount":

            features.append(
                float(
                    request.amount
                )
            )

        elif name == "balance":

            features.append(
                float(
                    payer["balance"]
                )
            )

    try:

        prediction = ML_MODEL.predict(
            [features]
        )[0]

        value = float(
            prediction
        )

        if 0 <= value <= 1:

            value *= 100.0

        return round(
            min(
                100.0,
                max(
                    0.0,
                    value
                )
            ),
            2
        )

    except Exception as exc:

        print(
            "[SecureFlow-AI] ML prediction "
            f"failed: {exc}"
        )

        return None


# ============================================================
# FINAL RISK CALCULATION
# ============================================================

def calculate_risk(
    request: PaymentRequest,
    payer: Dict[str, Any]
) -> Dict[str, Any]:

    signals = merge_signal_inputs(
        request
    )

    amount_info = (
        calculate_amount_deviation(
            request.payer_id,
            request.amount
        )
    )

    ml_score = ml_predict(
        request,
        payer,
        signals,
        amount_info
    )

    if ml_score is None:

        score = built_in_risk_model(
            signals,
            amount_info
        )

        model_used = (
            "SecureFlow behavioural engine"
        )

    else:

        score = ml_score

        model_used = "ML model"

    if score >= 80:

        decision = "BLOCK"
        status = "INSECURE_TRANSACTION"

    elif score >= 50:

        decision = "HOLD"
        status = "VERIFICATION_REQUIRED"

    else:

        decision = "ALLOW"
        status = "APPROVED"

    return {

        "risk_score": score,

        "decision": decision,

        "status": status,

        "model_used": model_used,

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
            ],

        "signals": signals
    }


# ============================================================
# DYNAMIC QUESTION GENERATOR
# ============================================================

def choose_dynamic_question(
    payer_id: str,
    request: PaymentRequest,
    amount_info: Dict[str, float],
    risk_score: float,
    recipient_seen: bool
) -> Dict[str, Any]:

    questions = QUESTION_DATA[
        payer_id
    ]

    signals = merge_signal_inputs(
        request
    )

    priority = []

    if signals["new_device"]:
        priority.append(
            "DEVICE_CONFIRM"
        )

    if (
        signals["unusual_location"]
        or
        signals["sudden_location_change"]
    ):
        priority.append(
            "LOCATION_CONFIRM"
        )

    if (
        signals["unknown_beneficiary"]
        or
        not recipient_seen
    ):
        priority.append(
            "RECIPIENT_CONFIRM"
        )

    if signals["previous_transaction"]:
        priority.append(
            "HISTORY_CONFIRM"
        )

    if (
        signals["typical_amount"]
        or
        amount_info["amount_risk"] > 0
    ):
        priority.append(
            "AMOUNT_CONFIRM"
        )

    if signals["transaction_frequency"]:
        priority.append(
            "HISTORY_CONFIRM"
        )

    if signals["time_anomaly"]:
        priority.append(
            "DOB_CONFIRM"
        )

    priority += [

        "RECIPIENT_CONFIRM",

        "HISTORY_CONFIRM",

        "COLLEGE_CONFIRM",

        "AREA_CONFIRM",

        "NEARBY_PLACE_CONFIRM",

        "DOB_CONFIRM"
    ]

    selected_code = None

    for code in priority:

        if any(
            q["code"] == code
            for q in questions
        ):

            selected_code = code
            break

    if selected_code is None:

        selected = random.choice(
            questions
        )

    else:

        selected = next(
            q
            for q in questions
            if q["code"] == selected_code
        )

    challenge_id = str(
        uuid.uuid4()
    )

    # IMPORTANT:
    # The expected answer remains on the backend.
    # It is never returned to the frontend.

    challenges[
        challenge_id
    ] = {

        "challenge_id":
            challenge_id,

        "payer_id":
            payer_id,

        "question_code":
            selected["code"],

        "question":
            selected["question"],

        "expected_answer":
            selected["answer"],

        "answer_type":
            selected["answer_type"],

        "risk_factor":
            selected["risk_factor"],

        "used":
            False,

        "created_at":
            datetime.now().isoformat(),

        # Preserve the actual held payment.

        "payment": {

            "recipient_name":
                request.recipient_name.strip(),

            "recipient_upi_id":
                request.recipient_upi_id.strip(),

            "amount":
                float(
                    request.amount
                ),

            "risk_score":
                risk_score
        }
    }

    return {

        "challenge_id":
            challenge_id,

        "question":
            selected["question"],

        "question_code":
            selected["code"],

        "answer_type":
            selected["answer_type"],

        "risk_factor":
            selected["risk_factor"]
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
            "online",

        "docs":
            "/docs"
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
                else
                "SecureFlow behavioural engine"
            ),

        "payers":
            len(users)
    }


# ============================================================
# GET ALL PAYERS
# ============================================================

@app.get("/users")
def get_users():

    return {

        "users": [

            public_user(
                users["U001"]
            ),

            public_user(
                users["U002"]
            ),

            public_user(
                users["U003"]
            ),

            public_user(
                users["U004"]
            )
        ]
    }


# ============================================================
# GET ONE PAYER
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
            public_user(
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

    return {

        "transactions":
            list(
                reversed(
                    transactions.get(
                        user_id,
                        []
                    )
                )
            )
    }


# ============================================================
# ANALYZE AND PAY
# ============================================================

@app.post("/analyze-payment")
def analyze_payment(
    request: PaymentRequest
):

    # --------------------------------------------------------
    # PAYER
    # --------------------------------------------------------

    if request.payer_id not in users:

        raise HTTPException(
            status_code=404,
            detail="Payer account not found."
        )

    payer = users[
        request.payer_id
    ]

    recipient_name = (
        request.recipient_name.strip()
    )

    recipient_upi = (
        request.recipient_upi_id.strip()
    )

    amount = float(
        request.amount
    )

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    if not recipient_name:

        raise HTTPException(
            status_code=400,
            detail="Recipient UPI name is required."
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
    # --------------------------------------------------------

    if amount > payer["balance"]:

        return {

            "success":
                False,

            "status":
                "INSUFFICIENT_BALANCE",

            "decision":
                "INSUFFICIENT_BALANCE",

            "risk_score":
                None,

            "message":
                (
                    "Insufficient balance. "
                    f"Available balance is "
                    f"₹{payer['balance']:,.2f}."
                ),

            "payer_id":
                request.payer_id,

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
    # RECIPIENT HISTORY
    # --------------------------------------------------------

    recipient_seen = (
        recipient_seen_before(
            request.payer_id,
            recipient_name,
            recipient_upi
        )
    )

    # --------------------------------------------------------
    # RISK ANALYSIS
    #
    # This is the point where the dashboard receives the
    # risk score.
    # --------------------------------------------------------

    risk = calculate_risk(
        request,
        payer
    )

    score = risk[
        "risk_score"
    ]

    common = {

        "payer_id":
            request.payer_id,

        "recipient_name":
            recipient_name,

        "recipient_upi_id":
            recipient_upi,

        "amount":
            amount,

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
            recipient_seen,

        "available_balance":
            money(
                payer["balance"]
            ),

        "signals":
            risk["signals"]
    }

    # ========================================================
    # RISK >= 80
    # ========================================================

    if score >= 80:

        transaction = {

            "transaction_id":
                "TX-" +
                uuid.uuid4().hex[
                    :12
                ].upper(),

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
                "Insecure transaction. Payment blocked."
        }

        transactions[
            request.payer_id
        ].append(
            transaction
        )

        return {

            **common,

            "success":
                False,

            "status":
                "INSECURE_TRANSACTION",

            "decision":
                "BLOCK",

            "message":
                (
                    "Insecure transaction. "
                    "Risk score is 80 or higher."
                )
        }

    # ========================================================
    # RISK 50-79
    # ========================================================

    if 50 <= score <= 79:

        challenge = (
            choose_dynamic_question(
                request.payer_id,
                request,
                {
                    "amount_risk":
                        risk["amount_risk"]
                },
                score,
                recipient_seen
            )
        )

        return {

            **common,

            "success":
                False,

            "status":
                "VERIFICATION_REQUIRED",

            "decision":
                "HOLD",

            "message":
                (
                    "Payment held for "
                    "additional verification."
                ),

            "challenge":
                challenge
        }

    # ========================================================
    # RISK 0-49
    # ========================================================

    payer["balance"] = money(
        payer["balance"] - amount
    )

    transaction = {

        "transaction_id":
            "TX-" +
            uuid.uuid4().hex[
                :12
            ].upper(),

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
        request.payer_id
    ].append(
        transaction
    )

    return {

        **common,

        "success":
            True,

        "status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "message":
            "Payment successful.",

        "new_balance":
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

    challenge_id = (
        verification.challenge_id.strip()
    )

    # --------------------------------------------------------
    # CHALLENGE CHECK
    # --------------------------------------------------------

    if challenge_id not in challenges:

        raise HTTPException(
            status_code=404,
            detail=(
                "Verification challenge "
                "not found or expired."
            )
        )

    challenge = challenges[
        challenge_id
    ]

    if challenge["used"]:

        raise HTTPException(
            status_code=400,
            detail=(
                "This verification challenge "
                "has already been used."
            )
        )

    payer_id = challenge[
        "payer_id"
    ]

    if payer_id not in users:

        raise HTTPException(
            status_code=404,
            detail="Payer account not found."
        )

    payer = users[
        payer_id
    ]

    # --------------------------------------------------------
    # ANSWER CHECK
    # --------------------------------------------------------

    expected = challenge[
        "expected_answer"
    ]

    supplied = (
        verification.answer.strip()
    )

    if challenge[
        "answer_type"
    ] == "YES_NO":

        supplied_normalized = (
            normalize_yes_no(
                supplied
            )
        )

        expected_normalized = (
            normalize_yes_no(
                expected
            )
        )

    else:

        supplied_normalized = (
            clean_text(
                supplied
            )
        )

        expected_normalized = (
            clean_text(
                expected
            )
        )

    correct = (
        supplied_normalized
        ==
        expected_normalized
    )

    # One-time challenge.

    challenge["used"] = True

    # ========================================================
    # WRONG ANSWER
    # ========================================================

    if not correct:

        return {

            "success":
                False,

            "correct":
                False,

            "status":
                "FAILED",

            "decision":
                "BLOCK",

            "message":
                (
                    "Payment failed. "
                    "The verification answer "
                    "was incorrect."
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
    # ========================================================

    payment = challenge[
        "payment"
    ]

    amount = float(
        payment["amount"]
    )

    # --------------------------------------------------------
    # CHECK BALANCE AGAIN
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
                    "but the payer no longer has "
                    "sufficient balance."
                ),

            "payer_id":
                payer_id,

            "new_balance":
                money(
                    payer["balance"]
                )
        }

    # --------------------------------------------------------
    # ONLY NOW DEDUCT THE BALANCE
    # --------------------------------------------------------

    payer["balance"] = money(
        payer["balance"] - amount
    )

    transaction = {

        "transaction_id":
            "TX-" +
            uuid.uuid4().hex[
                :12
            ].upper(),

        "recipient_name":
            payment[
                "recipient_name"
            ],

        "recipient_upi_id":
            payment[
                "recipient_upi_id"
            ],

        "amount":
            money(amount),

        "status":
            "SUCCESS",

        "transaction_status":
            "SUCCESS",

        "decision":
            "ALLOW",

        "risk_score":
            payment[
                "risk_score"
            ],

        "timestamp":
            datetime.now().isoformat(),

        "message":
            "Payment successful after verification."
    }

    transactions[
        payer_id
    ].append(
        transaction
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
            payment[
                "risk_score"
            ],

        "message":
            (
                "Verification successful. "
                "Payment completed."
            ),

        "payer_id":
            payer_id,

        "recipient_name":
            payment[
                "recipient_name"
            ],

        "recipient_upi_id":
            payment[
                "recipient_upi_id"
            ],

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

        "users": [

            public_user(
                users["U001"]
            ),

            public_user(
                users["U002"]
            ),

            public_user(
                users["U003"]
            ),

            public_user(
                users["U004"]
            )
        ]
    }


# ============================================================
# GET DYNAMIC QUESTIONS
# ============================================================

@app.get(
    "/dynamic-questions/{user_id}"
)
def get_dynamic_questions(
    user_id: str
):

    if user_id not in QUESTION_DATA:

        raise HTTPException(
            status_code=404,
            detail="Payer account not found."
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
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print()
    print("=" * 60)
    print("          SECUREFLOW-AI BACKEND")
    print("=" * 60)
    print()
    print(
        "Server: http://127.0.0.1:8000"
    )
    print(
        "Docs:   http://127.0.0.1:8000/docs"
    )
    print()
    print(
        "U001  Soumadip Das       ₹55,000"
    )
    print(
        "U002  Shubham Paul       ₹60,000"
    )
    print(
        "U003  Shubham Mukherjee  ₹50,000"
    )
    print(
        "U004  Tridip Debroy      ₹40,000"
    )
    print()
    print(
        "0-49   = ALLOW"
    )
    print(
        "50-79  = VERIFY"
    )
    print(
        "80-100 = BLOCK"
    )
    print()
    print(
        "Amount <= ₹1,000 = no amount anomaly"
    )
    print(
        "Amount > ₹1,000  = user-history analysis"
    )
    print()
    print("=" * 60)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
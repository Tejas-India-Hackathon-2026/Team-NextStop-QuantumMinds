# ============================================================
# SECUREFLOW-AI
# BACKEND API SERVER
# FastAPI + Random Forest
# ============================================================

from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="SecureFlow-AI API",
    description="Behavioural UPI Fraud Risk Detection API",
    version="1.0.0"
)


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# FEATURE DEFINITIONS
# ============================================================

FEATURE_COLUMNS = [
    "amount",
    "average_amount",
    "amount_ratio",
    "new_device",
    "new_location",
    "unusual_time",
    "new_beneficiary",
    "recent_transactions"
]


# ============================================================
# REQUEST MODELS
# ============================================================

class TransactionRequest(BaseModel):

    amount: float = Field(gt=0)

    average_amount: float = Field(gt=0)

    device: str

    location: str

    transaction_time: str

    beneficiary: str

    recent_transactions: int = Field(
        ge=0
    )


class VerificationRequest(BaseModel):

    answer: float

    correct_answer: float


# ============================================================
# SYNTHETIC TRAINING DATA
# ============================================================

def generate_training_data(n=5000):

    np.random.seed(42)

    rows = []

    for _ in range(n):

        average_amount = np.random.uniform(
            200,
            5000
        )

        amount = np.random.uniform(
            100,
            15000
        )

        new_device = np.random.binomial(
            1,
            0.15
        )

        new_location = np.random.binomial(
            1,
            0.18
        )

        unusual_time = np.random.binomial(
            1,
            0.12
        )

        new_beneficiary = np.random.binomial(
            1,
            0.15
        )

        recent_transactions = min(
            np.random.poisson(1.8),
            15
        )

        amount_ratio = (
            amount /
            max(average_amount, 1)
        )

        risk = 0

        if amount_ratio >= 5:
            risk += 3

        elif amount_ratio >= 3:
            risk += 2

        elif amount_ratio >= 2:
            risk += 1

        risk += new_device * 2
        risk += new_location * 2
        risk += unusual_time * 2
        risk += new_beneficiary * 2

        if recent_transactions >= 6:
            risk += 3

        elif recent_transactions >= 4:
            risk += 1

        risk += np.random.binomial(
            1,
            0.08
        )

        fraud = 1 if risk >= 5 else 0

        rows.append([
            amount,
            average_amount,
            amount_ratio,
            new_device,
            new_location,
            unusual_time,
            new_beneficiary,
            recent_transactions,
            fraud
        ])

    columns = FEATURE_COLUMNS + ["fraud"]

    return pd.DataFrame(
        rows,
        columns=columns
    )


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model():

    data = generate_training_data()

    X = data[FEATURE_COLUMNS]

    y = data["fraud"]

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=10,
        min_samples_split=5,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(
        X,
        y
    )

    return model


print("Training SecureFlow-AI model...")

MODEL = train_model()

print("Model ready.")


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features(transaction):

    average_amount = max(
        transaction.average_amount,
        1
    )

    amount_ratio = (
        transaction.amount /
        average_amount
    )

    new_device = (
        1
        if transaction.device.lower() == "new device"
        else 0
    )

    new_location = (
        1
        if transaction.location.lower() == "new location"
        else 0
    )

    new_beneficiary = (
        1
        if transaction.beneficiary.lower() == "new beneficiary"
        else 0
    )

    try:

        time_obj = datetime.strptime(
            transaction.transaction_time,
            "%I:%M %p"
        )

        hour = time_obj.hour

    except ValueError:

        hour = 12

    unusual_time = (
        1
        if hour >= 23 or hour < 5
        else 0
    )

    return {
        "amount": transaction.amount,
        "average_amount": average_amount,
        "amount_ratio": amount_ratio,
        "new_device": new_device,
        "new_location": new_location,
        "unusual_time": unusual_time,
        "new_beneficiary": new_beneficiary,
        "recent_transactions":
            transaction.recent_transactions
    }


# ============================================================
# BEHAVIOURAL RISK ENGINE
# ============================================================

def calculate_behaviour_risk(transaction):

    score = 0

    reasons: List[str] = []

    average_amount = max(
        transaction.average_amount,
        1
    )

    amount_ratio = (
        transaction.amount /
        average_amount
    )

    # Amount
    if amount_ratio >= 10:

        score += 30

        reasons.append(
            "Transaction amount is extremely higher than normal."
        )

    elif amount_ratio >= 5:

        score += 22

        reasons.append(
            "Transaction amount is significantly higher than normal."
        )

    elif amount_ratio >= 3:

        score += 15

        reasons.append(
            "Transaction amount is higher than usual."
        )

    elif amount_ratio >= 2:

        score += 8

        reasons.append(
            "Transaction amount is moderately higher than usual."
        )

    # Device
    if transaction.device.lower() == "new device":

        score += 18

        reasons.append(
            "New device detected."
        )

    # Location
    if transaction.location.lower() == "new location":

        score += 15

        reasons.append(
            "New location detected."
        )

    # Time
    try:

        time_obj = datetime.strptime(
            transaction.transaction_time,
            "%I:%M %p"
        )

        hour = time_obj.hour

        if hour >= 23 or hour < 5:

            score += 15

            reasons.append(
                "Transaction occurred during an unusual late-night period."
            )

    except ValueError:

        pass

    # Beneficiary
    if transaction.beneficiary.lower() == "new beneficiary":

        score += 12

        reasons.append(
            "New beneficiary detected."
        )

    # Frequency
    if transaction.recent_transactions >= 10:

        score += 20

        reasons.append(
            "Very high transaction frequency detected."
        )

    elif transaction.recent_transactions >= 6:

        score += 15

        reasons.append(
            "Unusually high transaction frequency detected."
        )

    elif transaction.recent_transactions >= 4:

        score += 8

        reasons.append(
            "Transaction frequency is higher than normal."
        )

    return min(
        max(score, 0),
        100
    ), reasons


# ============================================================
# ML RISK
# ============================================================

def calculate_ml_risk(transaction):

    features = extract_features(
        transaction
    )

    dataframe = pd.DataFrame(
        [features],
        columns=FEATURE_COLUMNS
    )

    probability = MODEL.predict_proba(
        dataframe
    )[0][1]

    return round(
        probability * 100,
        2
    )


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "service": "SecureFlow-AI",
        "model": "Random Forest"
    }


# ============================================================
# ANALYZE ENDPOINT
# ============================================================

@app.post("/analyze")
def analyze_transaction(
    transaction: TransactionRequest
):

    # Behavioural risk
    behaviour_score, reasons = (
        calculate_behaviour_risk(
            transaction
        )
    )

    # ML risk
    ml_score = calculate_ml_risk(
        transaction
    )

    # Hybrid score
    final_score = (
        behaviour_score * 0.60
        +
        ml_score * 0.40
    )

    final_score = round(
        min(max(final_score, 0)),
        2
    )

    # Decision
    if final_score >= 70:

        risk_level = "HIGH"

        decision = "BLOCK"

    elif final_score >= 40:

        risk_level = "MEDIUM"

        decision = "ALERT"

    else:

        risk_level = "LOW"

        decision = "ALLOW"

    if not reasons:

        reasons.append(
            "No significant suspicious behavioural signals detected."
        )

    return {

        "success": True,

        "transaction": {
            "amount": transaction.amount,
            "average_amount":
                transaction.average_amount,
            "device": transaction.device,
            "location": transaction.location,
            "transaction_time":
                transaction.transaction_time,
            "beneficiary":
                transaction.beneficiary,
            "recent_transactions":
                transaction.recent_transactions
        },

        "risk": {

            "behaviour_score":
                behaviour_score,

            "ml_score":
                ml_score,

            "final_score":
                final_score,

            "risk_level":
                risk_level
        },

        "decision": decision,

        "reasons": reasons,

        "verification_required":
            decision == "ALERT"
    }


# ============================================================
# VERIFICATION ENDPOINT
# ============================================================

@app.post("/verify")
def verify_transaction(
    verification: VerificationRequest
):

    is_valid = (
        abs(
            verification.answer
            -
            verification.correct_answer
        ) < 0.01
    )

    if is_valid:

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
# SERVER ENTRY POINT
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "backend_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
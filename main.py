from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Transaction(BaseModel):

    # A. Transaction behaviour
    amount: float
    unusual_frequency: bool
    unusual_time: bool
    high_velocity: bool

    # B. Device behaviour
    known_device: bool
    device_changed: bool

    # C. Location behaviour
    usual_location: bool
    sudden_location_change: bool

    # D. Relationship/history
    known_beneficiary: bool
    previous_transactions: bool
    typical_amount_with_beneficiary: bool
    beneficiary_matches_history: bool


@app.get("/")
def home():

    return {
        "message": "SecureFlow-AI Behavioural Engine"
    }


@app.post("/transaction")
def transaction(tx: Transaction):

    risk = 0
    reasons = []
    questions = []

    # A. Transaction behaviour

    if tx.amount > 10000:
        risk += 15
        reasons.append("High transaction amount")
        questions.append(
            f"Can you confirm a payment of ₹{tx.amount}?"
        )

    if tx.unusual_frequency:
        risk += 10
        reasons.append("Unusual transaction frequency")
        questions.append(
            "Have you made several transactions recently?"
        )

    if tx.unusual_time:
        risk += 10
        reasons.append("Unusual transaction time")
        questions.append(
            "Are you intentionally making this payment now?"
        )

    if tx.high_velocity:
        risk += 15
        reasons.append("High transaction velocity")
        questions.append(
            "Can you verify this rapid transaction activity?"
        )

    # B. Device behaviour

    if not tx.known_device:
        risk += 15
        reasons.append("Unknown device")
        questions.append(
            "Does this device belong to you?"
        )

    if tx.device_changed:
        risk += 10
        reasons.append("Device session changed")
        questions.append(
            "Did you recently switch devices?"
        )

    # C. Location behaviour

    if not tx.usual_location:
        risk += 10
        reasons.append("Unusual location")
        questions.append(
            "Can you confirm your current location?"
        )

    if tx.sudden_location_change:
        risk += 15
        reasons.append("Sudden location change")
        questions.append(
            "Did you recently travel?"
        )

    # D. Relationship/history

    if not tx.known_beneficiary:
        risk += 15
        reasons.append("Unknown beneficiary")
        questions.append(
            "Do you know this recipient personally?"
        )

    if not tx.previous_transactions:
        risk += 10
        reasons.append("No previous transaction history")
        questions.append(
            "Have you sent money to this person before?"
        )

    if not tx.typical_amount_with_beneficiary:
        risk += 10
        reasons.append(
            "Unusual amount for this beneficiary"
        )

    if not tx.beneficiary_matches_history:
        risk += 15
        reasons.append(
            "Beneficiary does not match historical behaviour"
        )

    if risk < 30:
        decision = "ALLOW"

    elif risk < 70:
        decision = "ALERT"

    else:
        decision = "BLOCK"

    return {
        "risk_score": risk,
        "decision": decision,
        "reasons": reasons,
        "ai_questions": questions
    }
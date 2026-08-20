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
        "message": "SecureFlow-AI Behavioural Engine is running"
    }


@app.post("/transaction")
def transaction(tx: Transaction):

    risk = 0
    reasons = []
    questions = []

    # Transaction behaviour

    if tx.amount > 10000:
        risk += 15
        reasons.append("Amount deviation")
        questions.append(
            f"Can you confirm a payment of ₹{tx.amount}?"
        )

    if tx.unusual_frequency:
        risk += 5

    if tx.unusual_time:
        risk += 10
        reasons.append("Time anomaly")
        questions.append(
            "Do you usually make transactions at this time?"
        )

    if tx.high_velocity:
        risk += 10
        reasons.append("Transaction velocity")
        questions.append(
            "Have you made multiple transactions recently?"
        )

    # Device behaviour

    device_flag = (
        (not tx.known_device)
        or tx.device_changed
    )

    if device_flag:
        risk += 20
        reasons.append("New device/session")
        questions.append(
            "Can you confirm that this device belongs to you?"
        )

    # Location behaviour

    location_flag = (
        (not tx.usual_location)
        or tx.sudden_location_change
    )

    if location_flag:
        risk += 15
        reasons.append("Location anomaly")
        questions.append(
            "Can you confirm your current location?"
        )

    # Relationship/history

    beneficiary_flag = not tx.known_beneficiary

    behaviour_flag = (
        (not tx.previous_transactions)
        or (not tx.typical_amount_with_beneficiary)
        or (not tx.beneficiary_matches_history)
    )

    if beneficiary_flag:
        risk += 15
        reasons.append("New beneficiary")
        questions.append(
            "Do you recognize this beneficiary?"
        )

    if behaviour_flag:
        risk += 15
        reasons.append("Behaviour deviation")
        questions.append(
            "Does this transaction match your historical behaviour?"
        )

    # Maximum score = 100

    risk = min(risk, 100)

    if risk <= 30:
        decision = "ALLOW"

    elif risk <= 70:
        decision = "ALERT"

    else:
        decision = "BLOCK"

    return {
        "risk_score": risk,
        "decision": decision,
        "transaction_delayed": risk >= 50,
        "reasons": reasons,
        "ai_questions": questions
    }
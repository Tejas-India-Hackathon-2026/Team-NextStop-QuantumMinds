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

    amount: float

    unusual_time: bool
    unusual_frequency: bool

    new_device: bool

    unusual_location: bool
    sudden_location_change: bool

    unknown_beneficiary: bool
    no_previous_transactions: bool
    unusual_beneficiary_amount: bool


@app.get("/")
def home():

    return {
        "message": "SecureFlow-AI UPI Fraud Detection Engine"
    }


@app.post("/transaction")
def analyze_transaction(tx: Transaction):

    risk = 0

    reasons = []

    questions = []

    if tx.amount > 10000:

        risk += 10

        reasons.append("Amount anomaly")

        questions.append(
            f"Can you confirm a payment of ₹{tx.amount}?"
        )

    if tx.unusual_time:

        risk += 7

        reasons.append("Time anomaly")

        questions.append(
            "Are you intentionally making this payment at this time?"
        )

    if tx.unusual_frequency:

        risk += 12

        reasons.append("Frequency anomaly")

        questions.append(
            "Have you made multiple payments recently?"
        )

    if tx.new_device:

        risk += 15

        reasons.append("New device detected")

        questions.append(
            "Does this device belong to you?"
        )

    if tx.unusual_location:

        risk += 15

        reasons.append("Unusual location")

        questions.append(
            "Can you confirm your current location?"
        )

    if tx.sudden_location_change:

        risk += 6

        reasons.append("Sudden location change")

        questions.append(
            "Did you recently travel?"
        )

    if tx.unknown_beneficiary:

        risk += 12

        reasons.append("Unknown beneficiary")

        questions.append(
            "Do you personally know this recipient?"
        )

    if tx.no_previous_transactions:

        risk += 13

        reasons.append("No previous transactions")

        questions.append(
            "Have you ever paid this recipient before?"
        )

    if tx.unusual_beneficiary_amount:

        risk += 10

        reasons.append(
            "Unusual amount for this beneficiary"
        )

        questions.append(
            "Is this amount typical for this recipient?"
        )

    if risk <= 30:

        decision = "ALLOW"

    elif risk <= 70:

        decision = "VERIFY"

    else:

        decision = "BLOCK"

    return {

        "risk_score": risk,

        "decision": decision,

        "reasons": reasons,

        "ai_questions": questions
    }
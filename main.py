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
    new_device: bool
    new_recipient: bool
    location_change: bool


@app.get("/")
def home():
    return {"message": "SecureFlow-AI is running"}


@app.post("/transaction")
def transaction(tx: Transaction):

    risk = 0
    reasons = []

    if tx.amount > 10000:
        risk += 20
        reasons.append("High amount")

    if tx.new_device:
        risk += 20
        reasons.append("New device")

    if tx.new_recipient:
        risk += 15
        reasons.append("New recipient")

    if tx.location_change:
        risk += 15
        reasons.append("Location change")

    if risk <= 30:
        decision = "ALLOW"
    elif risk <= 70:
        decision = "ALERT"
    else:
        decision = "BLOCK"

    ai_questions = []

    for reason in reasons:

        if reason == "High amount":
            ai_questions.append(
                f"Can you confirm the payment of ₹{tx.amount}?"
            )

        elif reason == "New device":
            ai_questions.append(
                "Please verify that this device belongs to you."
            )

        elif reason == "New recipient":
            ai_questions.append(
                "What is your relationship with this recipient?"
            )

        elif reason == "Location change":
            ai_questions.append(
                "Can you confirm your current location?"
            )

    return {
        "risk_score": risk,
        "decision": decision,
        "reasons": reasons,
        "transaction_delayed": risk >= 50,
        "ai_questions": ai_questions
    }
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SecureFlow-AI")


class Transaction(BaseModel):
    user_id: str
    recipient: str
    amount: float
    new_device: bool = False
    new_recipient: bool = False
    location_change: bool = False


@app.get("/")
def root():
    return {
        "message": "SecureFlow-AI backend is running"
    }


@app.post("/transaction")
def analyze_transaction(transaction: Transaction):

    risk_score = 0
    reasons = []

    if transaction.amount > 10000:
        risk_score += 20
        reasons.append("Amount unusually high")

    if transaction.new_device:
        risk_score += 20
        reasons.append("New device detected")

    if transaction.new_recipient:
        risk_score += 15
        reasons.append("New recipient detected")

    if transaction.location_change:
        risk_score += 15
        reasons.append("Location anomaly detected")

    if risk_score <= 30:
        decision = "ALLOW"
    elif risk_score <= 70:
        decision = "ALERT"
    else:
        decision = "BLOCK"

    return {
        "risk_score": risk_score,
        "decision": decision,
        "reasons": reasons
    }
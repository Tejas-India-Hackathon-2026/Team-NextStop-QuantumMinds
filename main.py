# routes/feedback.py

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class FraudFeedback(BaseModel):

    transaction_id: str
    user_id: str

    user_decision: str
    # "FRAUD" or "LEGITIMATE"

    system_decision: str
    risk_score: int


@router.post("/submit")
def submit_feedback(feedback: FraudFeedback):

    correct = (
        feedback.user_decision
        == feedback.system_decision
    )

    return {
        "transaction_id": feedback.transaction_id,
        "feedback_received": True,
        "model_decision_correct": correct
    }
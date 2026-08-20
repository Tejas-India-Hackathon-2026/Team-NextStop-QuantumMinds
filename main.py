# routes/transactions.py

from fastapi import APIRouter

from models.transaction import Transaction
from services.anomaly import calculate_z_score
from services.features import create_features
from services.risk_engine import calculate_risk_score, get_action

router = APIRouter()


@router.post("/check")
def check_transaction(transaction: Transaction):

    # Calculate behavioral anomaly
    z_score = calculate_z_score(
        transaction.amount,
        transaction.average_transaction_amount,
        max(transaction.average_transaction_amount * 0.2, 1)
    )

    features = create_features(transaction, z_score)

    # Temporary probability calculation.
    # Replace this with the trained XGBoost model.
    fraud_probability = min(
        0.99,
        abs(z_score) / 10
        + (0.10 if transaction.new_device else 0)
        + (0.10 if transaction.new_location else 0)
    )

    risk_score = calculate_risk_score(
        fraud_probability=fraud_probability,
        anomaly_score=z_score,
        new_device=transaction.new_device,
        new_location=transaction.new_location,
        failed_attempts=transaction.failed_attempts
    )

    action = get_action(risk_score)

    return {
        "transaction_id": transaction.transaction_id,
        "fraud_probability": round(fraud_probability, 3),
        "z_score": round(z_score, 2),
        "risk_score": risk_score,
        "action": action
    }
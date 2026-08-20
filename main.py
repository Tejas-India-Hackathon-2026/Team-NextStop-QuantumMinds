# services/velocity.py

from datetime import datetime, timedelta


def check_transaction_velocity(
    transactions,
    current_time=None,
    window_minutes=10,
    max_transactions=5
):
    """
    Detect unusually frequent transactions.
    """

    if current_time is None:
        current_time = datetime.utcnow()

    start_time = current_time - timedelta(minutes=window_minutes)

    recent_transactions = [
        tx for tx in transactions
        if tx["created_at"] >= start_time
    ]

    transaction_count = len(recent_transactions)

    suspicious = transaction_count >= max_transactions

    return {
        "transaction_count": transaction_count,
        "window_minutes": window_minutes,
        "suspicious": suspicious
    }
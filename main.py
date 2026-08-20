# risk_engine.py

from datetime import datetime
from typing import Dict, List, Tuple


def parse_time(time_string: str) -> datetime:
    """
    Convert time string such as '02:30 PM' into a datetime object.
    """

    return datetime.strptime(time_string, "%I:%M %p")


def calculate_risk(
    amount: float,
    average_amount: float,
    device: str,
    location: str,
    transaction_time: str,
    beneficiary: str,
    recent_transactions: int,
) -> Tuple[int, str, str, List[str]]:
    """
    Calculate behavioural risk.

    Returns:
        score       -> 0-100
        risk_level  -> LOW / MEDIUM / HIGH
        decision    -> ALLOW / ALERT / BLOCK
        reasons     -> list of explanations
    """

    score = 0
    reasons = []

    # ---------------------------------------------------------
    # 1. Amount anomaly
    # ---------------------------------------------------------

    if average_amount <= 0:
        average_amount = 1

    amount_ratio = amount / average_amount

    if amount_ratio >= 10:
        score += 30
        reasons.append(
            "Transaction amount is extremely higher than the user's normal amount."
        )

    elif amount_ratio >= 5:
        score += 22
        reasons.append(
            "Transaction amount is significantly higher than the user's normal amount."
        )

    elif amount_ratio >= 3:
        score += 15
        reasons.append(
            "Transaction amount is higher than the user's normal behaviour."
        )

    elif amount_ratio >= 2:
        score += 8
        reasons.append(
            "Transaction amount is moderately higher than usual."
        )

    # ---------------------------------------------------------
    # 2. Device anomaly
    # ---------------------------------------------------------

    if device.strip().lower() == "new device":
        score += 18
        reasons.append("New device detected.")

    # ---------------------------------------------------------
    # 3. Location anomaly
    # ---------------------------------------------------------

    if location.strip().lower() == "new location":
        score += 15
        reasons.append("Transaction originated from a new location.")

    # ---------------------------------------------------------
    # 4. Time anomaly
    # ---------------------------------------------------------

    try:
        transaction_dt = parse_time(transaction_time)
        hour = transaction_dt.hour

        # Unusual period: 11 PM - 5 AM
        if hour >= 23 or hour < 5:
            score += 15
            reasons.append(
                "Transaction occurred during an unusual late-night period."
            )

    except ValueError:
        # If time cannot be parsed, don't crash the application.
        pass

    # ---------------------------------------------------------
    # 5. Beneficiary anomaly
    # ---------------------------------------------------------

    if beneficiary.strip().lower() == "new beneficiary":
        score += 12
        reasons.append("New beneficiary detected.")

    # ---------------------------------------------------------
    # 6. Transaction frequency anomaly
    # ---------------------------------------------------------

    if recent_transactions >= 10:
        score += 20
        reasons.append(
            "Very high transaction frequency detected in the recent period."
        )

    elif recent_transactions >= 6:
        score += 15
        reasons.append(
            "Unusually high transaction frequency detected."
        )

    elif recent_transactions >= 4:
        score += 8
        reasons.append(
            "Transaction frequency is higher than normal."
        )

    # ---------------------------------------------------------
    # Keep score between 0 and 100
    # ---------------------------------------------------------

    score = min(max(score, 0), 100)

    # ---------------------------------------------------------
    # Risk classification
    # ---------------------------------------------------------

    if score >= 70:
        risk_level = "HIGH"
        decision = "BLOCK"

    elif score >= 40:
        risk_level = "MEDIUM"
        decision = "ALERT"

    else:
        risk_level = "LOW"
        decision = "ALLOW"

    # ---------------------------------------------------------
    # No suspicious reasons
    # ---------------------------------------------------------

    if not reasons:
        reasons.append(
            "No significant suspicious behavioural signals detected."
        )

    return score, risk_level, decision, reasons


def get_risk_features(
    amount: float,
    average_amount: float,
    device: str,
    location: str,
    transaction_time: str,
    beneficiary: str,
    recent_transactions: int,
) -> Dict:
    """
    Convert transaction information into ML-friendly features.
    """

    if average_amount <= 0:
        average_amount = 1

    amount_ratio = amount / average_amount

    # Device
    new_device = (
        1 if device.strip().lower() == "new device" else 0
    )

    # Location
    new_location = (
        1 if location.strip().lower() == "new location" else 0
    )

    # Beneficiary
    new_beneficiary = (
        1 if beneficiary.strip().lower() == "new beneficiary" else 0
    )

    # Time
    try:
        dt = parse_time(transaction_time)
        hour = dt.hour

    except ValueError:
        hour = 12

    unusual_time = (
        1 if hour >= 23 or hour < 5 else 0
    )

    return {
        "amount": float(amount),
        "average_amount": float(average_amount),
        "amount_ratio": float(amount_ratio),
        "new_device": int(new_device),
        "new_location": int(new_location),
        "unusual_time": int(unusual_time),
        "new_beneficiary": int(new_beneficiary),
        "recent_transactions": int(recent_transactions),
    }
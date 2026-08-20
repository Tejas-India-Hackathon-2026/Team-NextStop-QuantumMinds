# services/explanation.py

def explain_transaction(
    risk_score,
    z_score,
    new_device,
    new_location,
    failed_attempts,
    velocity_suspicious
):

    reasons = []

    if abs(z_score) >= 3:
        reasons.append(
            "Transaction amount is significantly "
            "different from normal behavior."
        )

    if new_device:
        reasons.append(
            "Transaction originated from a new device."
        )

    if new_location:
        reasons.append(
            "Transaction originated from a new location."
        )

    if failed_attempts > 0:
        reasons.append(
            "Multiple failed attempts were detected."
        )

    if velocity_suspicious:
        reasons.append(
            "Unusually high transaction frequency detected."
        )

    if not reasons:
        reasons.append(
            "No major behavioral anomaly detected."
        )

    return {
        "risk_score": risk_score,
        "reasons": reasons
    }
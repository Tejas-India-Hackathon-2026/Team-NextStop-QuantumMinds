# services/risk_engine.py

def calculate_risk_score(
    fraud_probability: float,
    anomaly_score: float,
    new_device: bool,
    new_location: bool,
    failed_attempts: int
):

    score = fraud_probability * 60

    # Behavioral anomaly
    score += min(abs(anomaly_score) * 5, 20)

    # New device
    if new_device:
        score += 10

    # New location
    if new_location:
        score += 5

    # Failed authentication/payment attempts
    score += min(failed_attempts * 2, 5)

    return min(round(score), 100)


def get_action(score: int):

    if score <= 30:
        return "ALLOW"

    elif score <= 70:
        return "ALERT"

    return "BLOCK"
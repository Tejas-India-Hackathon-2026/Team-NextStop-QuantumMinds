# services/anomaly.py

def calculate_z_score(
    current_amount: float,
    mean_amount: float,
    std_amount: float
) -> float:

    if std_amount == 0:
        return 0.0

    return (current_amount - mean_amount) / std_amount


def detect_amount_anomaly(z_score: float) -> bool:
    """
    A transaction is considered unusual when
    its amount is more than 3 standard deviations
    from the user's normal behavior.
    """

    return abs(z_score) >= 3
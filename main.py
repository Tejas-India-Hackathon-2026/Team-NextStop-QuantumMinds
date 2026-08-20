def final_risk_score(
        ml_score,
        amount_risk,
        device_risk,
        location_risk,
        recipient_risk
):

    final_score = (
        0.50 * ml_score +
        0.15 * amount_risk +
        0.15 * device_risk +
        0.10 * location_risk +
        0.10 * recipient_risk
    )

    return round(final_score, 2)
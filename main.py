# =========================================================
# SECUREFLOW-AI
# CODE 6 — AI / ML RISK SCORING ENGINE
# =========================================================


def calculate_risk_score(
    amount,
    average_amount,
    new_device,
    new_location,
    new_beneficiary,
    recent_transactions,
    unusual_time
):
    """
    Calculates a prototype fraud risk score from 0 to 100.

    Higher score = higher probability of suspicious activity.
    """

    score = 0
    reasons = []


    # -----------------------------------------------------
    # 1. TRANSACTION AMOUNT
    # -----------------------------------------------------

    if average_amount > 0:

        ratio = amount / average_amount

        if ratio >= 10:

            score += 30

            reasons.append(
                "Transaction amount is extremely high compared with normal behaviour."
            )

        elif ratio >= 5:

            score += 25

            reasons.append(
                "Transaction amount is significantly higher than normal."
            )

        elif ratio >= 3:

            score += 18

            reasons.append(
                "Transaction amount is considerably higher than normal."
            )

        elif ratio >= 2:

            score += 10

            reasons.append(
                "Transaction amount is higher than normal."
            )


    # -----------------------------------------------------
    # 2. NEW DEVICE
    # -----------------------------------------------------

    if new_device:

        score += 20

        reasons.append(
            "Transaction originated from an unknown device."
        )


    # -----------------------------------------------------
    # 3. NEW LOCATION
    # -----------------------------------------------------

    if new_location:

        score += 15

        reasons.append(
            "Transaction originated from an unusual location."
        )


    # -----------------------------------------------------
    # 4. NEW BENEFICIARY
    # -----------------------------------------------------

    if new_beneficiary:

        score += 15

        reasons.append(
            "Payment is being made to a new beneficiary."
        )


    # -----------------------------------------------------
    # 5. TRANSACTION FREQUENCY
    # -----------------------------------------------------

    if recent_transactions >= 8:

        score += 15

        reasons.append(
            "Very high transaction frequency detected."
        )

    elif recent_transactions >= 5:

        score += 8

        reasons.append(
            "Higher-than-normal transaction frequency detected."
        )


    # -----------------------------------------------------
    # 6. UNUSUAL TIME
    # -----------------------------------------------------

    if unusual_time:

        score += 15

        reasons.append(
            "Transaction occurred during unusual hours."
        )


    # -----------------------------------------------------
    # LIMIT SCORE TO 100
    # -----------------------------------------------------

    score = min(score, 100)


    # -----------------------------------------------------
    # RISK LEVEL
    # -----------------------------------------------------

    if score <= 30:

        risk_level = "LOW"

    elif score <= 70:

        risk_level = "MEDIUM"

    else:

        risk_level = "HIGH"


    return {

        "score": score,

        "risk_level": risk_level,

        "reasons": reasons

    }
@app.post("/transaction")
def transaction(tx: Transaction):

    risk = 0
    reasons = []
    questions = []

    # Transaction behaviour (maximum 35)

    if tx.amount > 10000:
        risk += 15
        reasons.append("Amount deviation")
        questions.append(
            f"Can you confirm a payment of ₹{tx.amount}?"
        )

    if tx.unusual_time:
        risk += 10
        reasons.append("Time anomaly")
        questions.append(
            "Are you intentionally making this payment now?"
        )

    if tx.high_velocity:
        risk += 10
        reasons.append("Transaction velocity")
        questions.append(
            "Have you made multiple transactions recently?"
        )

    # Device behaviour (maximum 20)

    if (not tx.known_device) or tx.device_changed:
        risk += 20
        reasons.append("New device/session")
        questions.append(
            "Can you confirm that this device belongs to you?"
        )

    # Location behaviour (maximum 15)

    if (not tx.usual_location) or tx.sudden_location_change:
        risk += 15
        reasons.append("Location anomaly")
        questions.append(
            "Can you confirm your current location?"
        )

    # Relationship/history (maximum 30)

    relationship_risk = 0

    if not tx.known_beneficiary:
        relationship_risk += 15

    if not tx.previous_transactions:
        relationship_risk += 5

    if not tx.typical_amount_with_beneficiary:
        relationship_risk += 5

    if not tx.beneficiary_matches_history:
        relationship_risk += 5

    if relationship_risk > 0:

        risk += min(15, relationship_risk)

        reasons.append("Behaviour deviation")

        questions.append(
            "Does this transaction match your historical behaviour?"
        )

    # Limit the score to 100

    risk = min(risk, 100)

    if risk <= 30:
        decision = "ALLOW"

    elif risk <= 70:
        decision = "ALERT"

    else:
        decision = "BLOCK"

    return {
        "risk_score": risk,
        "decision": decision,
        "reasons": reasons,
        "ai_questions": questions
    }
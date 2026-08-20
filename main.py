# =========================================================
# SECUREFLOW-AI
# CODE 7 — DECISION ENGINE
# =========================================================


def make_decision(risk_score):
    """
    Converts the risk score into a security decision.

    LOW risk     -> ALLOW
    MEDIUM risk  -> ALERT
    HIGH risk    -> BLOCK
    """

    # -----------------------------------------------------
    # LOW RISK
    # -----------------------------------------------------

    if risk_score <= 30:

        return {
            "decision": "ALLOW",
            "risk_level": "LOW",
            "message": "Transaction appears normal."
        }


    # -----------------------------------------------------
    # MEDIUM RISK
    # -----------------------------------------------------

    elif risk_score <= 70:

        return {
            "decision": "ALERT",
            "risk_level": "MEDIUM",
            "message": "Transaction requires user verification."
        }


    # -----------------------------------------------------
    # HIGH RISK
    # -----------------------------------------------------

    else:

        return {
            "decision": "BLOCK",
            "risk_level": "HIGH",
            "message": "Transaction blocked due to high fraud risk."
        }
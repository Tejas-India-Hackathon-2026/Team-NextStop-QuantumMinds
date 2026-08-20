# =========================================================
# BACKEND 14
# FRAUD PATTERN DETECTION
# =========================================================

@app.get("/api/fraud-patterns/{user_id}")
def detect_fraud_patterns(user_id: str):

    db = get_db()

    # -----------------------------------------------------
    # CHECK USER
    # -----------------------------------------------------

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    if user is None:

        db.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )


    # -----------------------------------------------------
    # GET RECENT TRANSACTIONS
    # -----------------------------------------------------

    transactions = db.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    ).fetchall()


    db.close()


    patterns = []


    # -----------------------------------------------------
    # NO TRANSACTIONS
    # -----------------------------------------------------

    if len(transactions) == 0:

        return {

            "success": True,

            "user_id": user_id,

            "fraud_detected": False,

            "risk_level": "LOW",

            "patterns": []

        }


    # -----------------------------------------------------
    # PATTERN 1:
    # MULTIPLE HIGH-RISK TRANSACTIONS
    # -----------------------------------------------------

    high_risk_count = 0

    for transaction in transactions:

        if transaction["risk_level"] == "HIGH":

            high_risk_count += 1


    if high_risk_count >= 3:

        patterns.append({

            "type":
                "REPEATED_HIGH_RISK",

            "severity":
                "HIGH",

            "message":
                "Multiple high-risk transactions detected."

        })


    # -----------------------------------------------------
    # PATTERN 2:
    # MULTIPLE BLOCKED TRANSACTIONS
    # -----------------------------------------------------

    blocked_count = 0

    for transaction in transactions:

        if transaction["decision"] == "BLOCK":

            blocked_count += 1


    if blocked_count >= 2:

        patterns.append({

            "type":
                "REPEATED_BLOCKED",

            "severity":
                "HIGH",

            "message":
                "Multiple transactions were blocked recently."

        })


    # -----------------------------------------------------
    # PATTERN 3:
    # UNUSUALLY HIGH AMOUNTS
    # -----------------------------------------------------

    average_amount = user["average_amount"]


    if average_amount > 0:

        for transaction in transactions:

            if transaction["amount"] >= (
                average_amount * 5
            ):

                patterns.append({

                    "type":
                        "UNUSUAL_AMOUNT",

                    "severity":
                        "HIGH",

                    "message":
                        "A transaction is significantly higher than the user's normal amount.",

                    "transaction_id":
                        transaction["id"],

                    "amount":
                        transaction["amount"]

                })

                break


    # -----------------------------------------------------
    # PATTERN 4:
    # UNKNOWN DEVICE
    # -----------------------------------------------------

    unknown_device_found = False


    for transaction in transactions:

        if (
            transaction["device"]
            and
            transaction["device"]
            != user["known_device"]
        ):

            unknown_device_found = True

            break


    if unknown_device_found:

        patterns.append({

            "type":
                "UNKNOWN_DEVICE",

            "severity":
                "MEDIUM",

            "message":
                "Transactions from an unknown device were detected."

        })


    # -----------------------------------------------------
    # PATTERN 5:
    # UNUSUAL LOCATION
    # -----------------------------------------------------

    unusual_location_found = False


    for transaction in transactions:

        if (
            transaction["location"]
            and
            transaction["location"]
            != user["known_location"]
        ):

            unusual_location_found = True

            break


    if unusual_location_found:

        patterns.append({

            "type":
                "UNUSUAL_LOCATION",

            "severity":
                "MEDIUM",

            "message":
                "Transactions from an unusual location were detected."

        })


    # -----------------------------------------------------
    # PATTERN 6:
    # NEW BENEFICIARY
    # -----------------------------------------------------

    new_beneficiary_found = False


    for transaction in transactions:

        if (
            transaction["beneficiary"]
            and
            transaction["beneficiary"]
            != user["known_beneficiary"]
        ):

            new_beneficiary_found = True

            break


    if new_beneficiary_found:

        patterns.append({

            "type":
                "NEW_BENEFICIARY",

            "severity":
                "MEDIUM",

            "message":
                "A transaction to a new beneficiary was detected."

        })


    # -----------------------------------------------------
    # DETERMINE OVERALL RISK
    # -----------------------------------------------------

    high_patterns = 0

    medium_patterns = 0


    for pattern in patterns:

        if pattern["severity"] == "HIGH":

            high_patterns += 1

        elif pattern["severity"] == "MEDIUM":

            medium_patterns += 1


    if high_patterns >= 1:

        overall_risk = "HIGH"

        fraud_detected = True

    elif medium_patterns >= 2:

        overall_risk = "MEDIUM"

        fraud_detected = True

    elif medium_patterns == 1:

        overall_risk = "MEDIUM"

        fraud_detected = False

    else:

        overall_risk = "LOW"

        fraud_detected = False


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "success": True,

        "user_id": user_id,

        "fraud_detected":
            fraud_detected,

        "risk_level":
            overall_risk,

        "patterns_detected":
            len(patterns),

        "patterns":
            patterns

    }
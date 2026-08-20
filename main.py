# =========================================================
# BACKEND 15
# TRANSACTION VELOCITY DETECTION
# =========================================================

from datetime import datetime, timedelta


@app.get("/api/velocity/{user_id}")
def transaction_velocity(user_id: str):

    db = get_db()

    # -----------------------------------------------------
    # CHECK USER
    # -----------------------------------------------------

    user = db.execute(
        """
        SELECT user_id
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
    # CURRENT TIME
    # -----------------------------------------------------

    now = datetime.now()


    # -----------------------------------------------------
    # TIME WINDOWS
    # -----------------------------------------------------

    five_minutes_ago = (
        now - timedelta(minutes=5)
    ).isoformat()

    fifteen_minutes_ago = (
        now - timedelta(minutes=15)
    ).isoformat()

    one_hour_ago = (
        now - timedelta(hours=1)
    ).isoformat()


    # -----------------------------------------------------
    # TRANSACTIONS IN LAST 5 MINUTES
    # -----------------------------------------------------

    last_5_minutes = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND created_at >= ?
        """,
        (
            user_id,
            five_minutes_ago
        )
    ).fetchone()["count"]


    # -----------------------------------------------------
    # TRANSACTIONS IN LAST 15 MINUTES
    # -----------------------------------------------------

    last_15_minutes = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND created_at >= ?
        """,
        (
            user_id,
            fifteen_minutes_ago
        )
    ).fetchone()["count"]


    # -----------------------------------------------------
    # TRANSACTIONS IN LAST 1 HOUR
    # -----------------------------------------------------

    last_hour = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND created_at >= ?
        """,
        (
            user_id,
            one_hour_ago
        )
    ).fetchone()["count"]


    # -----------------------------------------------------
    # TOTAL AMOUNT IN LAST HOUR
    # -----------------------------------------------------

    hourly_amount = db.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE user_id = ?
        AND created_at >= ?
        """,
        (
            user_id,
            one_hour_ago
        )
    ).fetchone()["amount"]


    db.close()


    # -----------------------------------------------------
    # DETERMINE VELOCITY RISK
    # -----------------------------------------------------

    reasons = []

    risk_level = "LOW"


    # Very high frequency

    if last_5_minutes >= 3:

        risk_level = "HIGH"

        reasons.append(
            "3 or more transactions detected "
            "within the last 5 minutes."
        )


    elif last_15_minutes >= 5:

        risk_level = "HIGH"

        reasons.append(
            "5 or more transactions detected "
            "within the last 15 minutes."
        )


    elif last_hour >= 8:

        risk_level = "MEDIUM"

        reasons.append(
            "8 or more transactions detected "
            "within the last hour."
        )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "success": True,

        "user_id": user_id,

        "velocity": {

            "last_5_minutes":
                last_5_minutes,

            "last_15_minutes":
                last_15_minutes,

            "last_hour":
                last_hour,

            "hourly_amount":
                round(
                    hourly_amount,
                    2
                )

        },

        "risk_level":
            risk_level,

        "suspicious":
            risk_level != "LOW",

        "reasons":
            reasons

    }
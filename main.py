# =========================================================
# BACKEND 12
# TRANSACTION STATISTICS API
# =========================================================

@app.get("/api/statistics/{user_id}")
def transaction_statistics(user_id: str):

    db = get_db()

    # ---------------------------------------------
    # Check user
    # ---------------------------------------------

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

    # ---------------------------------------------
    # Total transactions
    # ---------------------------------------------

    total = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["count"]

    # ---------------------------------------------
    # Total transaction amount
    # ---------------------------------------------

    total_amount = db.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["amount"]

    # ---------------------------------------------
    # Average transaction
    # ---------------------------------------------

    average_amount = db.execute(
        """
        SELECT COALESCE(AVG(amount), 0) AS amount
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["amount"]

    # ---------------------------------------------
    # Allowed
    # ---------------------------------------------

    allowed = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND decision = 'ALLOW'
        """,
        (user_id,)
    ).fetchone()["count"]

    # ---------------------------------------------
    # Alerts
    # ---------------------------------------------

    alert_count = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND decision = 'ALERT'
        """,
        (user_id,)
    ).fetchone()["count"]

    # ---------------------------------------------
    # Blocked
    # ---------------------------------------------

    blocked = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND decision = 'BLOCK'
        """,
        (user_id,)
    ).fetchone()["count"]

    # ---------------------------------------------
    # High-risk transactions
    # ---------------------------------------------

    high_risk = db.execute(
        """
        SELECT COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND risk_level = 'HIGH'
        """,
        (user_id,)
    ).fetchone()["count"]

    # ---------------------------------------------
    # Average risk score
    # ---------------------------------------------

    average_risk = db.execute(
        """
        SELECT COALESCE(AVG(risk_score), 0) AS score
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()["score"]

    db.close()

    # ---------------------------------------------
    # Fraud rate
    # ---------------------------------------------

    if total > 0:

        fraud_rate = (
            (alert_count + blocked) / total
        ) * 100

    else:

        fraud_rate = 0

    # ---------------------------------------------
    # Response
    # ---------------------------------------------

    return {

        "success": True,

        "user_id": user_id,

        "statistics": {

            "total_transactions":
                total,

            "total_amount":
                round(total_amount, 2),

            "average_transaction":
                round(average_amount, 2),

            "allowed":
                allowed,

            "alerts":
                alert_count,

            "blocked":
                blocked,

            "high_risk":
                high_risk,

            "average_risk_score":
                round(average_risk, 2),

            "fraud_rate":
                round(fraud_rate, 2)

        }

    }
# =========================================================
# SECUREFLOW-AI
# CODE 9 — TRANSACTION HISTORY & ALERTS
# =========================================================


# =========================================================
# GET TRANSACTION HISTORY
# =========================================================

@app.get("/api/transactions/{user_id}")
def get_transaction_history(
    user_id: str
):

    connection = get_database()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 50
        """,
        (user_id,)
    )

    transactions = cursor.fetchall()

    connection.close()


    return {

        "success": True,

        "user_id":
            user_id,

        "count":
            len(transactions),

        "transactions": [

            dict(transaction)

            for transaction in transactions

        ]

    }


# =========================================================
# GET HIGH-RISK ALERTS
# =========================================================

@app.get("/api/alerts/{user_id}")
def get_alerts(
    user_id: str
):

    connection = get_database()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions

        WHERE user_id = ?

        AND (
            risk_level = 'HIGH'
            OR decision = 'BLOCK'
            OR decision = 'ALERT'
        )

        ORDER BY id DESC

        LIMIT 20
        """,

        (user_id,)
    )

    alerts = cursor.fetchall()

    connection.close()


    return {

        "success": True,

        "user_id":
            user_id,

        "alert_count":
            len(alerts),

        "alerts": [

            dict(alert)

            for alert in alerts

        ]

    }


# =========================================================
# GET SINGLE TRANSACTION
# =========================================================

@app.get("/api/transaction/{transaction_id}")
def get_transaction(
    transaction_id: int
):

    connection = get_database()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE id = ?
        """,
        (transaction_id,)
    )

    transaction = cursor.fetchone()

    connection.close()


    if transaction is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )


    return {

        "success": True,

        "transaction":
            dict(transaction)

    }


# =========================================================
# DASHBOARD STATISTICS
# =========================================================

@app.get("/api/dashboard/{user_id}")
def get_dashboard(
    user_id: str
):

    connection = get_database()

    cursor = connection.cursor()


    # -----------------------------------------------------
    # TOTAL TRANSACTIONS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total = cursor.fetchone()["total"]


    # -----------------------------------------------------
    # ALLOWED TRANSACTIONS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM transactions

        WHERE user_id = ?

        AND decision = 'ALLOW'
        """,
        (user_id,)
    )

    allowed = cursor.fetchone()["total"]


    # -----------------------------------------------------
    # ALERT TRANSACTIONS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM transactions

        WHERE user_id = ?

        AND decision = 'ALERT'
        """,
        (user_id,)
    )

    alerts = cursor.fetchone()["total"]


    # -----------------------------------------------------
    # BLOCKED TRANSACTIONS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM transactions

        WHERE user_id = ?

        AND decision = 'BLOCK'
        """,
        (user_id,)
    )

    blocked = cursor.fetchone()["total"]


    # -----------------------------------------------------
    # HIGH RISK TRANSACTIONS
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT COUNT(*) AS total
        FROM transactions

        WHERE user_id = ?

        AND risk_level = 'HIGH'
        """,
        (user_id,)
    )

    high_risk = cursor.fetchone()["total"]


    connection.close()


    return {

        "success": True,

        "user_id":
            user_id,

        "statistics": {

            "total_transactions":
                total,

            "allowed":
                allowed,

            "alerts":
                alerts,

            "blocked":
                blocked,

            "high_risk":
                high_risk

        }

    }
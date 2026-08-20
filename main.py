# ============================================================
# SECUREFLOW-AI
# FASTAPI BACKEND
# VERSION 8.0
#
# Compatible with SecureFlow-AI SQLite Database
#
# Features:
# - User accounts
# - Recipients
# - Current balance
# - Transaction history
# - Risk scoring
# - ALLOW / ALERT / BLOCK
# - Dynamic security questions
# - User-specific expected answers
# - Challenge sessions
# - Balance update after successful payment
# - Dashboard
# - Analytics
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field

import sqlite3
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional


# ============================================================
# 1. CONFIGURATION
# ============================================================

DATABASE = "secureflow.db"

app = FastAPI(
    title="SecureFlow-AI Backend",
    description="Behavioural UPI Fraud Detection Backend",
    version="8.0"
)


# ============================================================
# 2. CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 3. DATABASE CONNECTION
# ============================================================

def get_db():
    conn = sqlite3.connect(
        DATABASE,
        timeout=30
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# 4. DATABASE HELPER
# ============================================================

def fetch_one(query, params=()):
    conn = get_db()

    try:
        cursor = conn.execute(query, params)
        row = cursor.fetchone()
        return row

    finally:
        conn.close()


def fetch_all(query, params=()):
    conn = get_db()

    try:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        return rows

    finally:
        conn.close()


# ============================================================
# 5. PYDANTIC MODELS
# ============================================================

class PaymentRequest(BaseModel):

    user_id: str

    recipient_id: str

    amount: float = Field(
        gt=0,
        description="Payment amount"
    )

    payment_location: str

    sender_device_name: Optional[str] = None


class ChallengeAnswerRequest(BaseModel):

    challenge_id: str

    answer: str


class LoginRequest(BaseModel):

    user_id: str


# ============================================================
# 6. ROOT
# ============================================================

@app.get("/")
def root():

    return {
        "application": "SecureFlow-AI",
        "version": "8.0",
        "status": "running",
        "database": DATABASE
    }


# ============================================================
# 7. HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    try:

        conn = get_db()

        conn.execute(
            "SELECT 1"
        )

        conn.close()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:

        return {
            "status": "error",
            "database": "disconnected",
            "error": str(e)
        }


# ============================================================
# 8. LOGIN / USER INFORMATION
# ============================================================

@app.post("/login")
def login(data: LoginRequest):

    user = fetch_one(
        """
        SELECT
            user_id,
            name,
            date_of_birth,
            college_name,
            living_area,
            known_device,
            common_location,
            initial_bank_balance,
            current_bank_balance,
            average_transaction,
            total_transactions
        FROM users
        WHERE user_id = ?
        """,
        (data.user_id,)
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "user": dict(user)
    }


# ============================================================
# 9. GET ALL USERS
# ============================================================

@app.get("/users")
def get_users():

    users = fetch_all(
        """
        SELECT
            user_id,
            name,
            date_of_birth,
            college_name,
            living_area,
            known_device,
            common_location,
            initial_bank_balance,
            current_bank_balance,
            average_transaction,
            total_transactions,
            created_at
        FROM users
        ORDER BY user_id
        """
    )

    return {
        "success": True,
        "count": len(users),
        "users": [dict(user) for user in users]
    }


# ============================================================
# 10. GET SINGLE USER
# ============================================================

@app.get("/users/{user_id}")
def get_user(user_id: str):

    user = fetch_one(
        """
        SELECT
            user_id,
            name,
            date_of_birth,
            college_name,
            living_area,
            known_device,
            common_location,
            initial_bank_balance,
            current_bank_balance,
            average_transaction,
            total_transactions,
            created_at
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "user": dict(user)
    }


# ============================================================
# 11. BALANCE
# ============================================================

@app.get("/users/{user_id}/balance")
def get_balance(user_id: str):

    user = fetch_one(
        """
        SELECT
            user_id,
            name,
            initial_bank_balance,
            current_bank_balance
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "user_id": user["user_id"],
        "name": user["name"],
        "initial_balance": user["initial_bank_balance"],
        "current_balance": user["current_bank_balance"],
        "currency": "INR"
    }


# ============================================================
# 12. GET RECIPIENTS
# ============================================================

@app.get("/recipients")
def get_recipients():

    recipients = fetch_all(
        """
        SELECT
            recipient_id,
            recipient_name,
            upi_id,
            recipient_device_name,
            recipient_location,
            recipient_type,
            created_at
        FROM recipients
        ORDER BY recipient_id
        """
    )

    return {
        "success": True,
        "count": len(recipients),
        "recipients": [dict(r) for r in recipients]
    }


# ============================================================
# 13. GET SINGLE RECIPIENT
# ============================================================

@app.get("/recipients/{recipient_id}")
def get_recipient(recipient_id: str):

    recipient = fetch_one(
        """
        SELECT
            recipient_id,
            recipient_name,
            upi_id,
            recipient_device_name,
            recipient_location,
            recipient_type,
            created_at
        FROM recipients
        WHERE recipient_id = ?
        """,
        (recipient_id,)
    )

    if not recipient:

        raise HTTPException(
            status_code=404,
            detail="Recipient not found"
        )

    return {
        "success": True,
        "recipient": dict(recipient)
    }


# ============================================================
# 14. USER RECIPIENT CONNECTION
# ============================================================

@app.get("/users/{user_id}/recipients")
def get_user_recipients(user_id: str):

    rows = fetch_all(
        """
        SELECT

            r.recipient_id,

            r.recipient_name,

            r.upi_id,

            r.recipient_device_name,

            r.recipient_location,

            r.recipient_type,

            c.previous_connection,

            c.connection_type,

            c.previous_transaction_count,

            c.connection_notes

        FROM recipients r

        LEFT JOIN sender_recipient_connections c

        ON r.recipient_id = c.recipient_id

        AND c.user_id = ?

        ORDER BY r.recipient_id
        """,
        (user_id,)
    )

    return {
        "success": True,
        "user_id": user_id,
        "recipients": [dict(row) for row in rows]
    }


# ============================================================
# 15. TRANSACTION HISTORY
# ============================================================

@app.get("/users/{user_id}/transactions")
def get_transactions(user_id: str):

    rows = fetch_all(
        """
        SELECT

            t.transaction_id,

            t.user_id,

            u.name AS sender_name,

            t.recipient_id,

            r.recipient_name,

            r.upi_id,

            t.amount,

            t.transaction_time,

            t.sender_device_name,

            t.recipient_device_name,

            t.payment_location,

            t.previous_location,

            t.previous_connection,

            t.transaction_status,

            t.risk_score,

            t.risk_decision,

            t.created_at

        FROM transactions t

        JOIN users u

        ON t.user_id = u.user_id

        JOIN recipients r

        ON t.recipient_id = r.recipient_id

        WHERE t.user_id = ?

        ORDER BY
            t.transaction_time DESC
        """,
        (user_id,)
    )

    return {
        "success": True,
        "user_id": user_id,
        "count": len(rows),
        "transactions": [dict(row) for row in rows]
    }


# ============================================================
# 16. SINGLE TRANSACTION
# ============================================================

@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):

    row = fetch_one(
        """
        SELECT

            t.transaction_id,

            t.user_id,

            u.name AS sender_name,

            t.recipient_id,

            r.recipient_name,

            r.upi_id,

            t.amount,

            t.transaction_time,

            t.sender_device_name,

            t.recipient_device_name,

            t.payment_location,

            t.previous_location,

            t.previous_connection,

            t.transaction_status,

            t.risk_score,

            t.risk_decision,

            t.created_at

        FROM transactions t

        JOIN users u
        ON t.user_id = u.user_id

        JOIN recipients r
        ON t.recipient_id = r.recipient_id

        WHERE t.transaction_id = ?
        """,
        (transaction_id,)
    )

    if not row:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "success": True,
        "transaction": dict(row)
    }


# ============================================================
# 17. USER SECURITY QUESTIONS
# ============================================================

@app.get("/users/{user_id}/security-questions")
def get_security_questions(user_id: str):

    rows = fetch_all(
        """
        SELECT

            q.question_id,

            q.question_code,

            q.question_text,

            q.risk_factor,

            q.expected_answer_type

        FROM security_questions q

        JOIN security_answers a

        ON q.question_id = a.question_id

        WHERE
            a.user_id = ?

            AND q.active = 1

        ORDER BY q.question_id
        """,
        (user_id,)
    )

    if not rows:

        raise HTTPException(
            status_code=404,
            detail="No security questions found for this user"
        )

    return {
        "success": True,
        "user_id": user_id,
        "questions": [dict(row) for row in rows]
    }


# ============================================================
# 18. RANDOM SECURITY QUESTION
# ============================================================

@app.get("/users/{user_id}/security-question/random")
def random_security_question(user_id: str):

    rows = fetch_all(
        """
        SELECT

            q.question_id,

            q.question_code,

            q.question_text,

            q.risk_factor,

            q.expected_answer_type

        FROM security_questions q

        JOIN security_answers a

        ON q.question_id = a.question_id

        WHERE
            a.user_id = ?

            AND q.active = 1
        """,
        (user_id,)
    )

    if not rows:

        raise HTTPException(
            status_code=404,
            detail="No security question available"
        )

    question = random.choice(rows)

    return {
        "success": True,
        "question": dict(question)
    }


# ============================================================
# 19. RISK CALCULATION
# ============================================================

def calculate_risk(
    user,
    recipient,
    connection,
    amount,
    payment_location,
    sender_device
):

    score = 0

    factors = []

    # --------------------------------------------------------
    # AMOUNT ANALYSIS
    # --------------------------------------------------------

    average_transaction = float(
        user["average_transaction"] or 0
    )

    if average_transaction > 0:

        if amount >= average_transaction * 3:

            score += 25

            factors.append(
                "Payment amount is significantly higher than normal"
            )

        elif amount >= average_transaction * 2:

            score += 15

            factors.append(
                "Payment amount is higher than usual"
            )

    # --------------------------------------------------------
    # BALANCE ANALYSIS
    # --------------------------------------------------------

    current_balance = float(
        user["current_bank_balance"]
    )

    if amount > current_balance:

        score += 50

        factors.append(
            "Insufficient account balance"
        )

    # --------------------------------------------------------
    # RECIPIENT CONNECTION
    # --------------------------------------------------------

    previous_connection = 0

    if connection:

        previous_connection = int(
            connection["previous_connection"]
        )

    if previous_connection == 0:

        score += 20

        factors.append(
            "No previous connection with recipient"
        )

    # --------------------------------------------------------
    # LOCATION ANALYSIS
    # --------------------------------------------------------

    common_location = (
        user["common_location"] or ""
    ).strip().lower()

    payment_loc = (
        payment_location or ""
    ).strip().lower()

    if common_location and payment_loc:

        if common_location != payment_loc:

            score += 15

            factors.append(
                "Payment location differs from usual location"
            )

    # --------------------------------------------------------
    # DEVICE ANALYSIS
    # --------------------------------------------------------

    known_device = (
        user["known_device"] or ""
    ).strip().lower()

    device = (
        sender_device or ""
    ).strip().lower()

    if device:

        if known_device and device != known_device:

            score += 25

            factors.append(
                "Payment initiated from an unknown device"
            )

    # --------------------------------------------------------
    # TIME ANALYSIS
    # --------------------------------------------------------

    current_hour = datetime.now().hour

    if current_hour >= 23 or current_hour < 5:

        score += 15

        factors.append(
            "Payment initiated during unusual hours"
        )

    # --------------------------------------------------------
    # CAP SCORE
    # --------------------------------------------------------

    score = min(score, 100)

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    if score >= 60:

        decision = "BLOCK"

    elif score >= 25:

        decision = "ALERT"

    else:

        decision = "ALLOW"

    return score, decision, factors


# ============================================================
# 20. CREATE NEW TRANSACTION
# ============================================================

def create_transaction(
    user_id,
    recipient_id,
    amount,
    payment_location,
    sender_device,
    status,
    risk_score,
    risk_decision
):

    conn = get_db()

    try:

        transaction_id = (
            "TX"
            + datetime.now().strftime("%Y%m%d%H%M%S")
            + uuid.uuid4().hex[:6].upper()
        )

        recipient = conn.execute(
            """
            SELECT
                recipient_device_name
            FROM recipients
            WHERE recipient_id = ?
            """,
            (recipient_id,)
        ).fetchone()

        if not recipient:

            raise HTTPException(
                status_code=404,
                detail="Recipient not found"
            )

        user = conn.execute(
            """
            SELECT
                common_location
            FROM users
            WHERE user_id = ?
            """,
            (user_id,)
        ).fetchone()

        previous_location = (
            user["common_location"]
            if user
            else None
        )

        connection = conn.execute(
            """
            SELECT
                previous_connection
            FROM sender_recipient_connections

            WHERE
                user_id = ?
                AND recipient_id = ?
            """,
            (
                user_id,
                recipient_id
            )
        ).fetchone()

        previous_connection = (
            int(connection["previous_connection"])
            if connection
            else 0
        )

        conn.execute(
            """
            INSERT INTO transactions
            (
                transaction_id,

                user_id,

                recipient_id,

                amount,

                transaction_time,

                sender_device_name,

                recipient_device_name,

                payment_location,

                previous_location,

                previous_connection,

                transaction_status,

                risk_score,

                risk_decision

            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                transaction_id,
                user_id,
                recipient_id,
                amount,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                sender_device,
                recipient["recipient_device_name"],
                payment_location,
                previous_location,
                previous_connection,
                status,
                risk_score,
                risk_decision
            )
        )

        conn.commit()

        return transaction_id

    finally:

        conn.close()


# ============================================================
# 21. PAYMENT ENDPOINT
# ============================================================

@app.post("/payment")
def make_payment(data: PaymentRequest):

    conn = get_db()

    try:

        # ----------------------------------------------------
        # START TRANSACTION
        # ----------------------------------------------------

        conn.execute("BEGIN IMMEDIATE")

        # ----------------------------------------------------
        # GET USER
        # ----------------------------------------------------

        user = conn.execute(
            """
            SELECT *

            FROM users

            WHERE user_id = ?
            """,
            (data.user_id,)
        ).fetchone()

        if not user:

            conn.rollback()

            raise HTTPException(
                status_code=404,
                detail="User not found"
            )

        # ----------------------------------------------------
        # GET RECIPIENT
        # ----------------------------------------------------

        recipient = conn.execute(
            """
            SELECT *

            FROM recipients

            WHERE recipient_id = ?
            """,
            (data.recipient_id,)
        ).fetchone()

        if not recipient:

            conn.rollback()

            raise HTTPException(
                status_code=404,
                detail="Recipient not found"
            )

        # ----------------------------------------------------
        # CHECK BALANCE
        # ----------------------------------------------------

        current_balance = float(
            user["current_bank_balance"]
        )

        if data.amount > current_balance:

            conn.rollback()

            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Insufficient balance",
                    "current_balance": current_balance,
                    "requested_amount": data.amount
                }
            )

        # ----------------------------------------------------
        # DEVICE
        # ----------------------------------------------------

        sender_device = (
            data.sender_device_name
            if data.sender_device_name
            else user["known_device"]
        )

        # ----------------------------------------------------
        # CONNECTION
        # ----------------------------------------------------

        connection = conn.execute(
            """
            SELECT *

            FROM sender_recipient_connections

            WHERE
                user_id = ?

                AND recipient_id = ?
            """,
            (
                data.user_id,
                data.recipient_id
            )
        ).fetchone()

        # ----------------------------------------------------
        # RISK ENGINE
        # ----------------------------------------------------

        risk_score, risk_decision, factors = calculate_risk(
            user,
            recipient,
            connection,
            data.amount,
            data.payment_location,
            sender_device
        )

        # ====================================================
        # CASE 1: BLOCK
        # ====================================================

        if risk_decision == "BLOCK":

            transaction_id = (
                "TX"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
                + uuid.uuid4().hex[:6].upper()
            )

            previous_location = user["common_location"]

            previous_connection = (
                int(connection["previous_connection"])
                if connection
                else 0
            )

            conn.execute(
                """
                INSERT INTO transactions
                (
                    transaction_id,
                    user_id,
                    recipient_id,
                    amount,
                    transaction_time,
                    sender_device_name,
                    recipient_device_name,
                    payment_location,
                    previous_location,
                    previous_connection,
                    transaction_status,
                    risk_score,
                    risk_decision
                )

                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'BLOCKED',
                    ?,
                    'BLOCK'
                )
                """,
                (
                    transaction_id,
                    data.user_id,
                    data.recipient_id,
                    data.amount,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    sender_device,
                    recipient["recipient_device_name"],
                    data.payment_location,
                    previous_location,
                    previous_connection,
                    risk_score
                )
            )

            conn.commit()

            return {
                "success": False,
                "status": "BLOCKED",
                "decision": "BLOCK",
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "risk_factors": factors,

                "amount": data.amount,

                "previous_balance": current_balance,

                "final_balance": current_balance,

                "message":
                    "Transaction blocked by SecureFlow-AI"
            }

        # ====================================================
        # CASE 2: ALERT
        # ====================================================

        if risk_decision == "ALERT":

            transaction_id = (
                "TX"
                + datetime.now().strftime(
                    "%Y%m%d%H%M%S"
                )
                + uuid.uuid4().hex[:6].upper()
            )

            previous_location = user["common_location"]

            previous_connection = (
                int(connection["previous_connection"])
                if connection
                else 0
            )

            conn.execute(
                """
                INSERT INTO transactions
                (
                    transaction_id,
                    user_id,
                    recipient_id,
                    amount,
                    transaction_time,
                    sender_device_name,
                    recipient_device_name,
                    payment_location,
                    previous_location,
                    previous_connection,
                    transaction_status,
                    risk_score,
                    risk_decision
                )

                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'PENDING',
                    ?,
                    'ALERT'
                )
                """,
                (
                    transaction_id,
                    data.user_id,
                    data.recipient_id,
                    data.amount,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    sender_device,
                    recipient["recipient_device_name"],
                    data.payment_location,
                    previous_location,
                    previous_connection,
                    risk_score
                )
            )

            # ------------------------------------------------
            # FIND SECURITY QUESTION
            # ------------------------------------------------

            question = conn.execute(
                """
                SELECT

                    q.question_id,

                    q.question_code,

                    q.question_text,

                    q.risk_factor,

                    q.expected_answer_type,

                    a.expected_answer

                FROM security_questions q

                JOIN security_answers a

                ON q.question_id = a.question_id

                WHERE

                    a.user_id = ?

                    AND q.active = 1

                ORDER BY RANDOM()

                LIMIT 1
                """,
                (data.user_id,)
            ).fetchone()

            if not question:

                conn.rollback()

                raise HTTPException(
                    status_code=500,
                    detail="Security question not configured"
                )

            # ------------------------------------------------
            # CREATE CHALLENGE
            # ------------------------------------------------

            challenge_id = str(
                uuid.uuid4()
            )

            created_at = datetime.now()

            expires_at = (
                created_at
                + timedelta(minutes=5)
            )

            conn.execute(
                """
                INSERT INTO challenge_sessions
                (
                    challenge_id,
                    user_id,
                    transaction_id,
                    question_id,
                    expected_answer,
                    created_at,
                    expires_at,
                    status
                )

                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    'PENDING'
                )
                """,
                (
                    challenge_id,
                    data.user_id,
                    transaction_id,
                    question["question_id"],
                    question["expected_answer"],
                    created_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    expires_at.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

            conn.commit()

            return {
                "success": True,

                "status": "ALERT",

                "decision": "ALERT",

                "transaction_id":
                    transaction_id,

                "challenge_id":
                    challenge_id,

                "risk_score":
                    risk_score,

                "risk_factors":
                    factors,

                "amount":
                    data.amount,

                "previous_balance":
                    current_balance,

                "final_balance":
                    current_balance,

                "security_question": {
                    "question_id":
                        question["question_id"],

                    "question_code":
                        question["question_code"],

                    "question_text":
                        question["question_text"],

                    "risk_factor":
                        question["risk_factor"],

                    "expected_answer_type":
                        question["expected_answer_type"]
                },

                "message":
                    "Additional verification required"
            }

        # ====================================================
        # CASE 3: ALLOW
        # ====================================================

        new_balance = (
            current_balance
            - data.amount
        )

        transaction_id = (
            "TX"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            + uuid.uuid4().hex[:6].upper()
        )

        previous_location = user["common_location"]

        previous_connection = (
            int(connection["previous_connection"])
            if connection
            else 0
        )

        # ----------------------------------------------------
        # INSERT TRANSACTION
        # ----------------------------------------------------

        conn.execute(
            """
            INSERT INTO transactions
            (
                transaction_id,
                user_id,
                recipient_id,
                amount,
                transaction_time,
                sender_device_name,
                recipient_device_name,
                payment_location,
                previous_location,
                previous_connection,
                transaction_status,
                risk_score,
                risk_decision
            )

            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                'SUCCESS',
                ?,
                'ALLOW'
            )
            """,
            (
                transaction_id,
                data.user_id,
                data.recipient_id,
                data.amount,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                sender_device,
                recipient["recipient_device_name"],
                data.payment_location,
                previous_location,
                previous_connection,
                risk_score
            )
        )

        # ----------------------------------------------------
        # UPDATE BALANCE
        # ----------------------------------------------------

        conn.execute(
            """
            UPDATE users

            SET
                current_bank_balance = ?,

                total_transactions =
                    total_transactions + 1

            WHERE user_id = ?
            """,
            (
                new_balance,
                data.user_id
            )
        )

        # ----------------------------------------------------
        # UPDATE CONNECTION
        # ----------------------------------------------------

        if connection:

            conn.execute(
                """
                UPDATE sender_recipient_connections

                SET
                    previous_connection = 1,

                    previous_transaction_count =
                        previous_transaction_count + 1

                WHERE
                    user_id = ?

                    AND recipient_id = ?
                """,
                (
                    data.user_id,
                    data.recipient_id
                )
            )

        else:

            conn.execute(
                """
                INSERT INTO sender_recipient_connections
                (
                    user_id,
                    recipient_id,
                    previous_connection,
                    connection_type,
                    previous_transaction_count,
                    connection_notes
                )

                VALUES
                (
                    ?,
                    ?,
                    1,
                    'Newly Used Recipient',
                    1,
                    'Created after successful payment'
                )
                """,
                (
                    data.user_id,
                    data.recipient_id
                )
            )

        conn.commit()

        return {
            "success": True,

            "status": "SUCCESS",

            "decision": "ALLOW",

            "transaction_id":
                transaction_id,

            "risk_score":
                risk_score,

            "risk_factors":
                factors,

            "amount":
                data.amount,

            "previous_balance":
                current_balance,

            "amount_deducted":
                data.amount,

            "final_balance":
                new_balance,

            "recipient": {
                "recipient_id":
                    recipient["recipient_id"],

                "recipient_name":
                    recipient["recipient_name"],

                "upi_id":
                    recipient["upi_id"]
            },

            "message":
                "Payment successful"
        }

    except HTTPException:

        raise

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        conn.close()


# ============================================================
# 22. VERIFY ALERT CHALLENGE
# ============================================================

@app.post("/payment/verify")
def verify_payment(data: ChallengeAnswerRequest):

    conn = get_db()

    try:

        conn.execute("BEGIN IMMEDIATE")

        # ----------------------------------------------------
        # GET CHALLENGE
        # ----------------------------------------------------

        challenge = conn.execute(
            """
            SELECT *

            FROM challenge_sessions

            WHERE challenge_id = ?
            """,
            (data.challenge_id,)
        ).fetchone()

        if not challenge:

            conn.rollback()

            raise HTTPException(
                status_code=404,
                detail="Challenge not found"
            )

        # ----------------------------------------------------
        # STATUS CHECK
        # ----------------------------------------------------

        if challenge["status"] != "PENDING":

            conn.rollback()

            raise HTTPException(
                status_code=400,
                detail="Challenge is no longer active"
            )

        # ----------------------------------------------------
        # EXPIRY CHECK
        # ----------------------------------------------------

        expires_at = datetime.strptime(
            challenge["expires_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        if datetime.now() > expires_at:

            conn.execute(
                """
                UPDATE challenge_sessions

                SET status = 'EXPIRED'

                WHERE challenge_id = ?
                """,
                (data.challenge_id,)
            )

            conn.commit()

            raise HTTPException(
                status_code=400,
                detail="Security challenge expired"
            )

        # ----------------------------------------------------
        # GET TRANSACTION
        # ----------------------------------------------------

        transaction = conn.execute(
            """
            SELECT *

            FROM transactions

            WHERE transaction_id = ?
            """,
            (challenge["transaction_id"],)
        ).fetchone()

        if not transaction:

            conn.rollback()

            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        # ----------------------------------------------------
        # NORMALIZE ANSWER
        # ----------------------------------------------------

        user_answer = (
            data.answer
            .strip()
            .upper()
        )

        expected_answer = (
            challenge["expected_answer"]
            .strip()
            .upper()
        )

        # ====================================================
        # CORRECT ANSWER
        # ====================================================

        if user_answer == expected_answer:

            user = conn.execute(
                """
                SELECT
                    current_bank_balance

                FROM users

                WHERE user_id = ?
                """,
                (challenge["user_id"],)
            ).fetchone()

            if not user:

                conn.rollback()

                raise HTTPException(
                    status_code=404,
                    detail="User not found"
                )

            current_balance = float(
                user["current_bank_balance"]
            )

            amount = float(
                transaction["amount"]
            )

            # ------------------------------------------------
            # BALANCE CHECK AGAIN
            # ------------------------------------------------

            if amount > current_balance:

                conn.execute(
                    """
                    UPDATE transactions

                    SET
                        transaction_status = 'BLOCKED',

                        risk_decision = 'BLOCK'

                    WHERE transaction_id = ?
                    """,
                    (challenge["transaction_id"],)
                )

                conn.execute(
                    """
                    UPDATE challenge_sessions

                    SET status = 'FAILED'

                    WHERE challenge_id = ?
                    """,
                    (data.challenge_id,)
                )

                conn.commit()

                return {
                    "success": False,

                    "status": "BLOCKED",

                    "message":
                        "Insufficient balance"
                }

            # ------------------------------------------------
            # NEW BALANCE
            # ------------------------------------------------

            new_balance = (
                current_balance - amount
            )

            # ------------------------------------------------
            # COMPLETE TRANSACTION
            # ------------------------------------------------

            conn.execute(
                """
                UPDATE transactions

                SET
                    transaction_status = 'SUCCESS',

                    risk_decision = 'ALLOW'

                WHERE transaction_id = ?
                """,
                (challenge["transaction_id"],)
            )

            # ------------------------------------------------
            # UPDATE BALANCE
            # ------------------------------------------------

            conn.execute(
                """
                UPDATE users

                SET
                    current_bank_balance = ?,

                    total_transactions =
                        total_transactions + 1

                WHERE user_id = ?
                """,
                (
                    new_balance,
                    challenge["user_id"]
                )
            )

            # ------------------------------------------------
            # UPDATE CHALLENGE
            # ------------------------------------------------

            conn.execute(
                """
                UPDATE challenge_sessions

                SET status = 'VERIFIED'

                WHERE challenge_id = ?
                """,
                (data.challenge_id,)
            )

            # ------------------------------------------------
            # UPDATE CONNECTION
            # ------------------------------------------------

            conn.execute(
                """
                UPDATE sender_recipient_connections

                SET

                    previous_connection = 1,

                    previous_transaction_count =
                        previous_transaction_count + 1

                WHERE

                    user_id = ?

                    AND recipient_id = ?
                """,
                (
                    challenge["user_id"],
                    transaction["recipient_id"]
                )
            )

            conn.commit()

            return {
                "success": True,

                "status": "SUCCESS",

                "message":
                    "Security verification successful. Payment completed.",

                "transaction_id":
                    transaction["transaction_id"],

                "amount":
                    amount,

                "previous_balance":
                    current_balance,

                "amount_deducted":
                    amount,

                "final_balance":
                    new_balance
            }

        # ====================================================
        # WRONG ANSWER
        # ====================================================

        else:

            conn.execute(
                """
                UPDATE transactions

                SET

                    transaction_status = 'BLOCKED',

                    risk_decision = 'BLOCK',

                    risk_score =
                        CASE
                            WHEN risk_score < 90
                            THEN risk_score + 20
                            ELSE 100
                        END

                WHERE transaction_id = ?
                """,
                (challenge["transaction_id"],)
            )

            conn.execute(
                """
                UPDATE challenge_sessions

                SET status = 'FAILED'

                WHERE challenge_id = ?
                """,
                (data.challenge_id,)
            )

            conn.commit()

            return {
                "success": False,

                "status": "BLOCKED",

                "message":
                    "Verification failed. Transaction blocked.",

                "transaction_id":
                    transaction["transaction_id"],

                "balance_changed":
                    False
            }

    except HTTPException:

        raise

    except Exception as e:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        conn.close()


# ============================================================
# 23. USER ACCOUNT SUMMARY
# ============================================================

@app.get("/users/{user_id}/summary")
def account_summary(user_id: str):

    row = fetch_one(
        """
        SELECT *

        FROM user_account_summary

        WHERE user_id = ?
        """,
        (user_id,)
    )

    if not row:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "summary": dict(row)
    }


# ============================================================
# 24. DASHBOARD
# ============================================================

@app.get("/dashboard/{user_id}")
def dashboard(user_id: str):

    user = fetch_one(
        """
        SELECT *

        FROM users

        WHERE user_id = ?
        """,
        (user_id,)
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    transactions = fetch_all(
        """
        SELECT

            t.transaction_id,

            r.recipient_name,

            r.upi_id,

            t.amount,

            t.transaction_time,

            t.transaction_status,

            t.risk_score,

            t.risk_decision

        FROM transactions t

        JOIN recipients r

        ON t.recipient_id = r.recipient_id

        WHERE t.user_id = ?

        ORDER BY
            t.transaction_time DESC

        LIMIT 10
        """,
        (user_id,)
    )

    return {
        "success": True,

        "user": {
            "user_id":
                user["user_id"],

            "name":
                user["name"],

            "current_balance":
                user["current_bank_balance"],

            "initial_balance":
                user["initial_bank_balance"]
        },

        "recent_transactions":
            [dict(t) for t in transactions]
    }


# ============================================================
# 25. ANALYTICS
# ============================================================

@app.get("/analytics")
def analytics():

    total_transactions = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions
        """
    )["total"]

    successful = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE transaction_status = 'SUCCESS'
        """
    )["total"]

    pending = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE transaction_status = 'PENDING'
        """
    )["total"]

    blocked = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE transaction_status = 'BLOCKED'
        """
    )["total"]

    held = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE transaction_status = 'HELD'
        """
    )["total"]

    alerts = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE risk_decision = 'ALERT'
        """
    )["total"]

    allowed = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE risk_decision = 'ALLOW'
        """
    )["total"]

    risk_block = fetch_one(
        """
        SELECT COUNT(*) AS total

        FROM transactions

        WHERE risk_decision = 'BLOCK'
        """
    )["total"]

    total_money = fetch_one(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            ) AS total

        FROM transactions

        WHERE transaction_status = 'SUCCESS'
        """
    )["total"]

    return {

        "success": True,

        "analytics": {

            "total_transactions":
                total_transactions,

            "successful_transactions":
                successful,

            "pending_transactions":
                pending,

            "held_transactions":
                held,

            "blocked_transactions":
                blocked,

            "allow_cases":
                allowed,

            "alert_cases":
                alerts,

            "block_cases":
                risk_block,

            "successful_money_transferred":
                total_money
        }
    }


# ============================================================
# 26. RISK DISTRIBUTION
# ============================================================

@app.get("/analytics/risk-distribution")
def risk_distribution():

    rows = fetch_all(
        """
        SELECT

            risk_decision,

            COUNT(*) AS count,

            COALESCE(
                SUM(amount),
                0
            ) AS total_amount

        FROM transactions

        GROUP BY risk_decision

        ORDER BY risk_decision
        """
    )

    return {
        "success": True,
        "risk_distribution": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# 27. STATUS DISTRIBUTION
# ============================================================

@app.get("/analytics/status-distribution")
def status_distribution():

    rows = fetch_all(
        """
        SELECT

            transaction_status,

            COUNT(*) AS count,

            COALESCE(
                SUM(amount),
                0
            ) AS total_amount

        FROM transactions

        GROUP BY transaction_status

        ORDER BY transaction_status
        """
    )

    return {
        "success": True,
        "status_distribution": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# 28. FRAUD ALERTS
# ============================================================

@app.get("/fraud-alerts")
def fraud_alerts():

    rows = fetch_all(
        """
        SELECT

            t.transaction_id,

            t.user_id,

            u.name AS sender_name,

            r.recipient_name,

            r.upi_id,

            t.amount,

            t.transaction_time,

            t.payment_location,

            t.previous_location,

            t.previous_connection,

            t.transaction_status,

            t.risk_score,

            t.risk_decision

        FROM transactions t

        JOIN users u

        ON t.user_id = u.user_id

        JOIN recipients r

        ON t.recipient_id = r.recipient_id

        WHERE

            t.risk_decision IN
            (
                'ALERT',
                'BLOCK'
            )

        ORDER BY
            t.risk_score DESC,
            t.transaction_time DESC
        """
    )

    return {
        "success": True,
        "count": len(rows),
        "fraud_alerts": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# 29. LIVE MONITOR
# ============================================================

@app.get("/live-monitor")
def live_monitor():

    rows = fetch_all(
        """
        SELECT

            t.transaction_id,

            t.user_id,

            u.name AS sender_name,

            t.recipient_id,

            r.recipient_name,

            t.amount,

            t.transaction_time,

            t.payment_location,

            t.transaction_status,

            t.risk_score,

            t.risk_decision

        FROM transactions t

        JOIN users u

        ON t.user_id = u.user_id

        JOIN recipients r

        ON t.recipient_id = r.recipient_id

        ORDER BY
            t.transaction_time DESC

        LIMIT 50
        """
    )

    return {
        "success": True,
        "transactions": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# 30. REPORTS
# ============================================================

@app.get("/reports")
def reports():

    users = fetch_all(
        """
        SELECT

            user_id,

            name,

            initial_bank_balance,

            current_bank_balance,

            total_transactions,

            average_transaction

        FROM users

        ORDER BY user_id
        """
    )

    return {
        "success": True,

        "report": {

            "generated_at":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

            "users":
                [dict(u) for u in users]
        }
    }


# ============================================================
# 31. CHALLENGE STATUS
# ============================================================

@app.get("/challenge/{challenge_id}")
def challenge_status(challenge_id: str):

    challenge = fetch_one(
        """
        SELECT

            challenge_id,

            user_id,

            transaction_id,

            question_id,

            created_at,

            expires_at,

            status

        FROM challenge_sessions

        WHERE challenge_id = ?
        """,
        (challenge_id,)
    )

    if not challenge:

        raise HTTPException(
            status_code=404,
            detail="Challenge not found"
        )

    return {
        "success": True,
        "challenge": dict(challenge)
    }


# ============================================================
# 32. TRANSACTION COUNTS
# ============================================================

@app.get("/statistics/transactions")
def transaction_statistics():

    rows = fetch_all(
        """
        SELECT

            user_id,

            COUNT(*) AS transaction_count,

            SUM(
                CASE
                    WHEN risk_decision = 'ALLOW'
                    THEN 1
                    ELSE 0
                END
            ) AS allow_count,

            SUM(
                CASE
                    WHEN risk_decision = 'ALERT'
                    THEN 1
                    ELSE 0
                END
            ) AS alert_count,

            SUM(
                CASE
                    WHEN risk_decision = 'BLOCK'
                    THEN 1
                    ELSE 0
                END
            ) AS block_count

        FROM transactions

        GROUP BY user_id

        ORDER BY user_id
        """
    )

    return {
        "success": True,
        "statistics": [
            dict(row)
            for row in rows
        ]
    }


# ============================================================
# 33. START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
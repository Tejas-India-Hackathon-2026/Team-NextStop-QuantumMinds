from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from pathlib import Path
from datetime import datetime
import sqlite3
import uuid
import random


# ============================================================
# SECUREFLOW-AI
# Behavioural UPI Fraud Detection Backend
# ============================================================

app = FastAPI(
    title="SecureFlow-AI",
    description="Behavioural UPI fraud detection and dynamic verification engine",
    version="5.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "SecureFlow-AI5.db"


def db():
    """
    Open the SQLite database.
    """
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                f"Database not found: {DB_PATH.name}. "
                f"Put SecureFlow-AI5.db in the same folder as main.py."
            )
        )

    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    con = db()
    cur = con.cursor()

    # --------------------------------------------------------
    # Create a live balance column.
    #
    # Original database contains:
    # initial_bank_balance
    #
    # We keep that value untouched and create:
    # current_bank_balance
    # --------------------------------------------------------

    columns = cur.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    column_names = [row["name"] for row in columns]

    if "current_bank_balance" not in column_names:

        cur.execute(
            """
            ALTER TABLE users
            ADD COLUMN current_bank_balance REAL
            """
        )

        cur.execute(
            """
            UPDATE users
            SET current_bank_balance = initial_bank_balance
            WHERE current_bank_balance IS NULL
            """
        )

    else:

        # Make sure old NULL values are initialized.
        cur.execute(
            """
            UPDATE users
            SET current_bank_balance = initial_bank_balance
            WHERE current_bank_balance IS NULL
            """
        )

    # --------------------------------------------------------
    # Challenge table
    #
    # Stores dynamic questions temporarily.
    # --------------------------------------------------------

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS challenge_sessions (

            challenge_id TEXT PRIMARY KEY,

            user_id TEXT NOT NULL,

            recipient_id TEXT,

            transaction_amount REAL NOT NULL,

            risk_score INTEGER NOT NULL,

            question TEXT NOT NULL,

            expected_answer TEXT NOT NULL,

            created_at TEXT NOT NULL,

            expires_at TEXT NOT NULL,

            status TEXT NOT NULL DEFAULT 'PENDING'

        )
        """
    )

    # --------------------------------------------------------
    # Demo transaction table
    # We continue using the original transactions table.
    # --------------------------------------------------------

    con.commit()
    con.close()


@app.on_event("startup")
def startup():

    initialize_database()


# ============================================================
# MODELS
# ============================================================

class AnalyzePayment(BaseModel):

    # Payer selected from database
    payer_id: str

    # Recipient can be selected/entered by judge
    recipient_name: str
    recipient_upi_id: str

    amount: float = Field(gt=0)

    # --------------------------------------------------------
    # FINAL RISK ENGINE CONTROLS
    #
    # Amount deviation is deliberately NOT included.
    # The backend determines amount risk automatically.
    # --------------------------------------------------------

    new_beneficiary: bool = False

    new_device_session: bool = False

    location_anomaly: bool = False

    time_anomaly: bool = False

    transaction_velocity: bool = False

    behaviour_deviation: bool = False


class VerifyChallenge(BaseModel):

    challenge_id: str

    answer: str


# ============================================================
# BASIC ROUTES
# ============================================================

@app.get("/")
def home():

    return {
        "application": "SecureFlow-AI",
        "status": "online",
        "database": DB_PATH.name,
        "engine": "Behavioural Risk Engine",
        "thresholds": {
            "allow": "0-44",
            "hold": "45-69",
            "block": "70+"
        }
    }


@app.get("/health")
def health():

    con = db()

    try:

        con.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected"
        }

    finally:

        con.close()


# ============================================================
# GET PAYERS
# ============================================================

@app.get("/users")
def get_users():

    con = db()

    try:

        rows = con.execute(
            """
            SELECT
                user_id,
                name,
                living_area,
                common_location,
                known_device,
                current_bank_balance
            FROM users
            ORDER BY name
            """
        ).fetchall()

        return {
            "users": [dict(row) for row in rows]
        }

    finally:

        con.close()


# ============================================================
# GET RECIPIENTS
# ============================================================

@app.get("/recipients")
def get_recipients():

    con = db()

    try:

        rows = con.execute(
            """
            SELECT
                recipient_id,
                recipient_name,
                upi_id,
                recipient_device_name,
                recipient_location,
                recipient_type
            FROM recipients
            ORDER BY recipient_name
            """
        ).fetchall()

        return {
            "recipients": [dict(row) for row in rows]
        }

    finally:

        con.close()


# ============================================================
# FIND RECIPIENT
# ============================================================

def find_recipient(
    con,
    recipient_name: str,
    recipient_upi_id: str
):

    row = con.execute(
        """
        SELECT *
        FROM recipients
        WHERE LOWER(upi_id) = LOWER(?)

           OR LOWER(recipient_name) = LOWER(?)

        LIMIT 1
        """,
        (
            recipient_upi_id.strip(),
            recipient_name.strip()
        )
    ).fetchone()

    return row


# ============================================================
# FIND PAYER
# ============================================================

def find_payer(con, payer_id):

    row = con.execute(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (payer_id,)
    ).fetchone()

    return row


# ============================================================
# RECIPIENT-SPECIFIC HISTORY
# ============================================================

def get_relationship(
    con,
    user_id,
    recipient_id
):

    return con.execute(
        """
        SELECT *
        FROM sender_recipient_connections

        WHERE user_id = ?
        AND recipient_id = ?

        LIMIT 1
        """,
        (
            user_id,
            recipient_id
        )
    ).fetchone()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def get_transaction_history(
    con,
    user_id,
    recipient_id
):

    return con.execute(
        """
        SELECT
            amount,
            transaction_time,
            payment_location,
            previous_location,
            transaction_status

        FROM transactions

        WHERE user_id = ?
        AND recipient_id = ?

        ORDER BY transaction_time DESC
        """,
        (
            user_id,
            recipient_id
        )
    ).fetchall()


# ============================================================
# AI AMOUNT RISK
#
# This replaces the old "Amount deviation ON/OFF" switch.
#
# The score is automatically calculated from:
#
# 1. Payer's average transaction amount
# 2. Payer-recipient transaction history
# 3. Typical amount sent to this recipient
#
# Maximum = 9
# ============================================================

def calculate_amount_risk(
    con,
    payer,
    recipient_id,
    amount
):

    history = get_transaction_history(
        con,
        payer["user_id"],
        recipient_id
    )

    historical_amounts = [
        float(row["amount"])
        for row in history
        if row["transaction_status"] == "SUCCESS"
    ]

    # --------------------------------------------------------
    # If there is recipient-specific history,
    # use that as the strongest signal.
    # Otherwise use payer average.
    # --------------------------------------------------------

    if historical_amounts:

        typical_amount = sum(
            historical_amounts
        ) / len(historical_amounts)

    else:

        typical_amount = float(
            payer["average_transaction"] or 0
        )

    if typical_amount <= 0:

        return 0, typical_amount

    ratio = amount / typical_amount

    # --------------------------------------------------------
    # Amount risk is intentionally below 10.
    # --------------------------------------------------------

    if ratio <= 1.50:

        score = 0

    elif ratio <= 2.00:

        score = 3

    elif ratio <= 2.50:

        score = 5

    elif ratio <= 3.00:

        score = 7

    else:

        score = 9

    return score, typical_amount


# ============================================================
# AI QUESTION GENERATOR
#
# Questions are generated from actual database facts.
#
# No hard-coded Rahul/Amit/etc. is assumed.
# ============================================================

def generate_dynamic_questions(
    con,
    payer,
    recipient,
    relationship,
    amount,
    amount_risk
):

    questions = []

    payer_name = payer["name"]

    recipient_name = recipient["recipient_name"]

    recipient_location = recipient["recipient_location"]

    payer_location = payer["common_location"]

    payer_device = payer["known_device"]

    previous_count = 0

    previous_connection = False

    if relationship:

        previous_count = int(
            relationship["previous_transaction_count"] or 0
        )

        previous_connection = bool(
            relationship["previous_connection"]
        )

    # --------------------------------------------------------
    # Question 1: Recipient relationship
    # --------------------------------------------------------

    if not previous_connection or previous_count == 0:

        questions.append(
            {
                "question":
                    f"Is {recipient_name} a recipient you have "
                    f"previously paid?",
                "answer":
                    "no"
            }
        )

    else:

        questions.append(
            {
                "question":
                    f"You have previously paid {recipient_name}. "
                    f"Do you recognize this recipient?",
                "answer":
                    "yes"
            }
        )

    # --------------------------------------------------------
    # Question 2: Recipient type
    # --------------------------------------------------------

    recipient_type = recipient["recipient_type"]

    questions.append(
        {
            "question":
                f"What type of recipient is {recipient_name} "
                f"according to your payment history? "
                f"(Example: {recipient_type})",
            "answer":
                str(recipient_type).lower()
        }
    )

    # --------------------------------------------------------
    # Question 3: Location
    # --------------------------------------------------------

    questions.append(
        {
            "question":
                f"What is your usual payment location?",
            "answer":
                str(payer_location).lower()
        }
    )

    # --------------------------------------------------------
    # Question 4: Recipient location
    # --------------------------------------------------------

    questions.append(
        {
            "question":
                f"What location is associated with "
                f"{recipient_name}?",
            "answer":
                str(recipient_location).lower()
        }
    )

    # --------------------------------------------------------
    # Question 5: Known device
    # --------------------------------------------------------

    questions.append(
        {
            "question":
                f"What device is normally associated with "
                f"your account?",
            "answer":
                str(payer_device).lower()
        }
    )

    # --------------------------------------------------------
    # Question 6: Transaction amount behaviour
    # --------------------------------------------------------

    history = get_transaction_history(
        con,
        payer["user_id"],
        recipient["recipient_id"]
    )

    successful_amounts = [
        float(row["amount"])
        for row in history
        if row["transaction_status"] == "SUCCESS"
    ]

    if successful_amounts:

        typical = sum(successful_amounts) / len(
            successful_amounts
        )

        questions.append(
            {
                "question":
                    f"Approximately how much do you usually "
                    f"send to {recipient_name}?",
                "answer":
                    str(round(typical))
            }
        )

    # --------------------------------------------------------
    # Select a small random set.
    #
    # This makes the challenge dynamic.
    # --------------------------------------------------------

    # We don't want too many questions during a demo.

    if len(questions) > 3:

        selected = random.sample(
            questions,
            3
        )

    else:

        selected = questions

    return selected


# ============================================================
# ANSWER NORMALIZATION
# ============================================================

def normalize_answer(value):

    value = str(value).strip().lower()

    replacements = {
        "yes": "yes",
        "y": "yes",
        "yeah": "yes",
        "yep": "yes",

        "no": "no",
        "n": "no",
        "nope": "no"
    }

    return replacements.get(
        value,
        value
    )


# ============================================================
# ANSWER VERIFICATION
# ============================================================

def answer_is_correct(
    user_answer,
    expected_answer
):

    user_answer = normalize_answer(
        user_answer
    )

    expected_answer = normalize_answer(
        expected_answer
    )

    # --------------------------------------------------------
    # Direct match
    # --------------------------------------------------------

    if user_answer == expected_answer:

        return True

    # --------------------------------------------------------
    # Numeric answers
    # --------------------------------------------------------

    try:

        user_number = float(
            user_answer
        )

        expected_number = float(
            expected_answer
        )

        # Allow a reasonable approximation for
        # "approximately how much".
        if abs(
            user_number - expected_number
        ) <= max(
            100,
            expected_number * 0.15
        ):

            return True

    except ValueError:

        pass

    # --------------------------------------------------------
    # Text containment
    # --------------------------------------------------------

    if (
        expected_answer in user_answer
        or user_answer in expected_answer
    ):

        return True

    return False


# ============================================================
# SCORE HELPERS
# ============================================================

def add_signal(
    signals,
    name,
    points,
    active
):

    if active:

        signals.append(
            {
                "name": name,
                "score": points
            }
        )


# ============================================================
# ANALYZE + PAY
#
# IMPORTANT:
# Risk score is calculated ONLY when this endpoint is called.
# ============================================================

@app.post("/analyze-payment")
def analyze_payment(
    payment: AnalyzePayment
):

    con = db()

    try:

        # ====================================================
        # FIND PAYER
        # ====================================================

        payer = find_payer(
            con,
            payment.payer_id
        )

        if not payer:

            raise HTTPException(
                status_code=404,
                detail="Payer not found in database."
            )

        # ====================================================
        # FIND RECIPIENT
        # ====================================================

        recipient = find_recipient(
            con,
            payment.recipient_name,
            payment.recipient_upi_id
        )

        if not recipient:

            # Unknown recipient is allowed to be entered.
            # It becomes a high-risk/new-beneficiary signal,
            # but no recipient-specific challenge can be created.
            recipient_id = None

        else:

            recipient_id = recipient["recipient_id"]

        # ====================================================
        # BALANCE CHECK
        # ====================================================

        balance = float(
            payer["current_bank_balance"] or 0
        )

        if payment.amount > balance:

            return {
                "status": "FAILED",
                "decision": "INSUFFICIENT_BALANCE",
                "message":
                    "Payment failed because the payer does "
                    "not have sufficient balance.",
                "balance": balance
            }

        # ====================================================
        # RELATIONSHIP
        # ====================================================

        relationship = None

        if recipient_id:

            relationship = get_relationship(
                con,
                payment.payer_id,
                recipient_id
            )

        # ====================================================
        # AUTOMATIC AMOUNT RISK
        # ====================================================

        if recipient_id:

            amount_risk, typical_amount = (
                calculate_amount_risk(
                    con,
                    payer,
                    recipient_id,
                    payment.amount
                )
            )

        else:

            # Completely unknown recipient:
            # compare with payer's average.
            typical_amount = float(
                payer["average_transaction"] or 0
            )

            if typical_amount > 0:

                ratio = (
                    payment.amount /
                    typical_amount
                )

                if ratio <= 1.5:
                    amount_risk = 0
                elif ratio <= 2:
                    amount_risk = 3
                elif ratio <= 2.5:
                    amount_risk = 5
                elif ratio <= 3:
                    amount_risk = 7
                else:
                    amount_risk = 9

            else:

                amount_risk = 0

        # ====================================================
        # RISK ENGINE
        # ====================================================

        signals = []

        # ----------------------------------------------------
        # Amount
        # ----------------------------------------------------

        if amount_risk > 0:

            signals.append(
                {
                    "name": "Amount deviation",
                    "score": amount_risk
                }
            )

        # ----------------------------------------------------
        # New beneficiary +15
        # ----------------------------------------------------

        new_beneficiary = (
            payment.new_beneficiary
        )

        # Database can also identify a new relationship.

        if relationship:

            if not bool(
                relationship["previous_connection"]
            ):

                new_beneficiary = True

        elif recipient_id:

            new_beneficiary = True

        add_signal(
            signals,
            "New beneficiary",
            15,
            new_beneficiary
        )

        # ----------------------------------------------------
        # New device/session +20
        # ----------------------------------------------------

        add_signal(
            signals,
            "New device/session",
            20,
            payment.new_device_session
        )

        # ----------------------------------------------------
        # Location anomaly +15
        # ----------------------------------------------------

        add_signal(
            signals,
            "Location anomaly",
            15,
            payment.location_anomaly
        )

        # ----------------------------------------------------
        # Time anomaly +10
        # ----------------------------------------------------

        add_signal(
            signals,
            "Time anomaly",
            10,
            payment.time_anomaly
        )

        # ----------------------------------------------------
        # Transaction velocity +10
        # ----------------------------------------------------

        add_signal(
            signals,
            "Transaction velocity",
            10,
            payment.transaction_velocity
        )

        # ----------------------------------------------------
        # Behaviour deviation +15
        # ----------------------------------------------------

        add_signal(
            signals,
            "Behaviour deviation",
            15,
            payment.behaviour_deviation
        )

        # ====================================================
        # TOTAL SCORE
        # ====================================================

        risk_score = sum(
            item["score"]
            for item in signals
        )

        # Maximum possible with current design:
        # 9 + 15 + 20 + 15 + 10 + 10 + 15 = 94

        risk_score = min(
            risk_score,
            94
        )

        # ====================================================
        # 70+ = BLOCK IMMEDIATELY
        # ====================================================

        if risk_score >= 70:

            transaction_id = (
                "T" +
                uuid.uuid4().hex[:10].upper()
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            con.execute(
                """
                INSERT INTO transactions (

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
                    created_at

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    payer["user_id"],
                    recipient_id,
                    payment.amount,
                    now,
                    payer["known_device"],
                    recipient["recipient_device_name"]
                    if recipient else "UNKNOWN",
                    payer["common_location"],
                    payer["common_location"],
                    int(
                        bool(
                            relationship["previous_connection"]
                        )
                    )
                    if relationship else 0,
                    "BLOCKED",
                    now
                )
            )

            con.commit()

            return {
                "status": "BLOCKED",
                "decision": "BLOCK",
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "signals": signals,
                "message":
                    "Payment blocked immediately because "
                    "the risk score is 70 or above."
            }

        # ====================================================
        # 0-44 = PAY
        # ====================================================

        if risk_score <= 44:

            transaction_id = (
                "T" +
                uuid.uuid4().hex[:10].upper()
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # ------------------------------------------------
            # Deduct balance
            # ------------------------------------------------

            new_balance = (
                balance -
                payment.amount
            )

            con.execute(
                """
                UPDATE users

                SET current_bank_balance = ?

                WHERE user_id = ?
                """,
                (
                    new_balance,
                    payer["user_id"]
                )
            )

            # ------------------------------------------------
            # Save transaction
            # ------------------------------------------------

            con.execute(
                """
                INSERT INTO transactions (

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
                    created_at

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    payer["user_id"],
                    recipient_id,
                    payment.amount,
                    now,
                    payer["known_device"],
                    recipient["recipient_device_name"]
                    if recipient else "UNKNOWN",
                    payer["common_location"],
                    payer["common_location"],
                    int(
                        bool(
                            relationship["previous_connection"]
                        )
                    )
                    if relationship else 0,
                    "SUCCESS",
                    now
                )
            )

            con.commit()

            return {
                "status": "SUCCESS",
                "decision": "PAY",
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "signals": signals,
                "previous_balance": balance,
                "new_balance": new_balance,
                "message":
                    "Payment completed successfully."
            }

        # ====================================================
        # 45-69 = HOLD + DYNAMIC QUESTION
        # ====================================================

        # At this point payment is NOT deducted.

        if not recipient:

            # We cannot create a recipient-specific
            # challenge when the recipient doesn't exist
            # in the database.

            return {
                "status": "HELD",
                "decision": "HOLD",
                "risk_score": risk_score,
                "signals": signals,
                "message":
                    "Payment is on hold. The recipient is not "
                    "present in the behavioural database, so "
                    "recipient-specific verification data is "
                    "unavailable."
            }

        # ----------------------------------------------------
        # Generate questions from database
        # ----------------------------------------------------

        generated_questions = (
            generate_dynamic_questions(
                con,
                payer,
                recipient,
                relationship,
                payment.amount,
                amount_risk
            )
        )

        # ----------------------------------------------------
        # Create a challenge for the FIRST question.
        #
        # The frontend can submit the answer.
        # If correct -> payment completes.
        # If incorrect -> payment cancelled.
        # ----------------------------------------------------

        selected_question = generated_questions[0]

        challenge_id = (
            "CH-" +
            uuid.uuid4().hex[:12].upper()
        )

        now = datetime.now()

        created_at = now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        expires_at = (
            now.replace(
                second=0
            )
        )

        # 5 minute challenge
        from datetime import timedelta

        expires_at = (
            now +
            timedelta(minutes=5)
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        con.execute(
            """
            INSERT INTO challenge_sessions (

                challenge_id,
                user_id,
                recipient_id,
                transaction_amount,
                risk_score,
                question,
                expected_answer,
                created_at,
                expires_at,
                status

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                challenge_id,
                payer["user_id"],
                recipient["recipient_id"],
                payment.amount,
                risk_score,
                selected_question["question"],
                selected_question["answer"],
                created_at,
                expires_at,
                "PENDING"
            )
        )

        con.commit()

        return {
            "status": "HELD",
            "decision": "HOLD",
            "risk_score": risk_score,
            "signals": signals,

            "challenge": {
                "challenge_id": challenge_id,
                "question":
                    selected_question["question"],
                "expires_in_seconds": 300
            },

            "message":
                "Payment temporarily held for dynamic "
                "behavioural verification."
        }

    finally:

        con.close()


# ============================================================
# VERIFY DYNAMIC QUESTION
# ============================================================

@app.post("/verify-challenge")
def verify_challenge(
    verification: VerifyChallenge
):

    con = db()

    try:

        challenge = con.execute(
            """
            SELECT *
            FROM challenge_sessions

            WHERE challenge_id = ?

            LIMIT 1
            """,
            (
                verification.challenge_id
            )
        ).fetchone()

        if not challenge:

            raise HTTPException(
                status_code=404,
                detail="Verification challenge not found."
            )

        # ====================================================
        # CHECK STATUS
        # ====================================================

        if challenge["status"] != "PENDING":

            return {
                "status": "FAILED",
                "decision": "CANCEL",
                "message":
                    "This verification challenge is no longer active."
            }

        # ====================================================
        # CHECK EXPIRATION
        # ====================================================

        expires_at = datetime.strptime(
            challenge["expires_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        if datetime.now() > expires_at:

            con.execute(
                """
                UPDATE challenge_sessions

                SET status = 'EXPIRED'

                WHERE challenge_id = ?
                """,
                (
                    verification.challenge_id
                )
            )

            con.commit()

            return {
                "status": "FAILED",
                "decision": "CANCEL",
                "message":
                    "Verification expired. Payment cancelled."
            }

        # ====================================================
        # CHECK ANSWER
        # ====================================================

        correct = answer_is_correct(
            verification.answer,
            challenge["expected_answer"]
        )

        # ====================================================
        # WRONG ANSWER = CANCEL
        # ====================================================

        if not correct:

            con.execute(
                """
                UPDATE challenge_sessions

                SET status = 'FAILED'

                WHERE challenge_id = ?
                """,
                (
                    verification.challenge_id
                )
            )

            # ------------------------------------------------
            # Record failed transaction
            # ------------------------------------------------

            transaction_id = (
                "T" +
                uuid.uuid4().hex[:10].upper()
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            payer = con.execute(
                """
                SELECT *
                FROM users

                WHERE user_id = ?
                """,
                (
                    challenge["user_id"],
                )
            ).fetchone()

            recipient = con.execute(
                """
                SELECT *
                FROM recipients

                WHERE recipient_id = ?
                """,
                (
                    challenge["recipient_id"],
                )
            ).fetchone()

            relationship = get_relationship(
                con,
                challenge["user_id"],
                challenge["recipient_id"]
            )

            con.execute(
                """
                INSERT INTO transactions (

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
                    created_at

                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    challenge["user_id"],
                    challenge["recipient_id"],
                    challenge["transaction_amount"],
                    now,
                    payer["known_device"]
                    if payer else "UNKNOWN",
                    recipient["recipient_device_name"]
                    if recipient else "UNKNOWN",
                    payer["common_location"]
                    if payer else "UNKNOWN",
                    payer["common_location"]
                    if payer else "UNKNOWN",
                    int(
                        bool(
                            relationship["previous_connection"]
                        )
                    )
                    if relationship else 0,
                    "CANCELLED",
                    now
                )
            )

            con.commit()

            return {
                "status": "FAILED",
                "decision": "CANCEL",
                "risk_score":
                    challenge["risk_score"],
                "transaction_id":
                    transaction_id,
                "message":
                    "Verification failed. Payment cancelled immediately."
            }

        # ====================================================
        # CORRECT ANSWER = COMPLETE PAYMENT
        # ====================================================

        payer = con.execute(
            """
            SELECT *
            FROM users

            WHERE user_id = ?
            """,
            (
                challenge["user_id"],
            )
        ).fetchone()

        if not payer:

            raise HTTPException(
                status_code=404,
                detail="Payer no longer exists."
            )

        recipient = con.execute(
            """
            SELECT *
            FROM recipients

            WHERE recipient_id = ?
            """,
            (
                challenge["recipient_id"],
            )
        ).fetchone()

        # ----------------------------------------------------
        # LIVE BALANCE
        # ----------------------------------------------------

        current_balance = float(
            payer["current_bank_balance"] or 0
        )

        payment_amount = float(
            challenge["transaction_amount"]
        )

        if payment_amount > current_balance:

            con.execute(
                """
                UPDATE challenge_sessions

                SET status = 'FAILED'

                WHERE challenge_id = ?
                """,
                (
                    verification.challenge_id
                )
            )

            con.commit()

            return {
                "status": "FAILED",
                "decision": "CANCEL",
                "message":
                    "Payment cancelled because the balance "
                    "is no longer sufficient."
            }

        # ----------------------------------------------------
        # Deduct money
        # ----------------------------------------------------

        new_balance = (
            current_balance -
            payment_amount
        )

        con.execute(
            """
            UPDATE users

            SET current_bank_balance = ?

            WHERE user_id = ?
            """,
            (
                new_balance,
                challenge["user_id"]
            )
        )

        # ----------------------------------------------------
        # Mark challenge completed
        # ----------------------------------------------------

        con.execute(
            """
            UPDATE challenge_sessions

            SET status = 'VERIFIED'

            WHERE challenge_id = ?
            """,
            (
                verification.challenge_id
            )
        )

        # ----------------------------------------------------
        # Record transaction
        # ----------------------------------------------------

        transaction_id = (
            "T" +
            uuid.uuid4().hex[:10].upper()
        )

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        relationship = get_relationship(
            con,
            challenge["user_id"],
            challenge["recipient_id"]
        )

        con.execute(
            """
            INSERT INTO transactions (

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
                created_at

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                challenge["user_id"],
                challenge["recipient_id"],
                payment_amount,
                now,
                payer["known_device"],
                recipient["recipient_device_name"]
                if recipient else "UNKNOWN",
                payer["common_location"],
                payer["common_location"],
                int(
                    bool(
                        relationship["previous_connection"]
                    )
                )
                if relationship else 0,
                "SUCCESS",
                now
            )
        )

        con.commit()

        return {
            "status": "SUCCESS",
            "decision": "PAY",
            "risk_score":
                challenge["risk_score"],
            "transaction_id":
                transaction_id,
            "previous_balance":
                current_balance,
            "new_balance":
                new_balance,
            "message":
                "Verification successful. Payment completed."
        }

    finally:

        con.close()


# ============================================================
# GET CURRENT BALANCE
# ============================================================

@app.get("/balance/{user_id}")
def get_balance(user_id: str):

    con = db()

    try:

        user = find_payer(
            con,
            user_id
        )

        if not user:

            raise HTTPException(
                status_code=404,
                detail="Payer not found."
            )

        return {
            "user_id": user["user_id"],
            "name": user["name"],
            "balance":
                float(
                    user["current_bank_balance"] or 0
                )
        }

    finally:

        con.close()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.get("/transactions/{user_id}")
def get_transactions(user_id: str):

    con = db()

    try:

        rows = con.execute(
            """
            SELECT
                t.transaction_id,
                t.amount,
                t.transaction_time,
                t.transaction_status,
                r.recipient_name,
                r.upi_id

            FROM transactions t

            LEFT JOIN recipients r
                ON t.recipient_id = r.recipient_id

            WHERE t.user_id = ?

            ORDER BY
                t.transaction_time DESC

            LIMIT 50
            """,
            (
                user_id
            )
        ).fetchall()

        return {
            "transactions":
                [dict(row) for row in rows]
        }

    finally:

        con.close()


# ============================================================
# RUN
# ============================================================

# Do NOT use app.run().
#
# Start with:
#
# python -m uvicorn main:app --reload
#
# ============================================================
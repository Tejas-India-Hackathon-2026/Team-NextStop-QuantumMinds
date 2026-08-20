from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import uuid
import random


# ============================================================
# SECUREFLOW-AI
# Behavioural UPI Fraud Detection + Dynamic Verification
# ============================================================

app = FastAPI(
    title="SecureFlow-AI",
    description="Behavioural UPI fraud detection and dynamic verification engine",
    version="6.0"
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


def get_db():
    """
    Open the SQLite database.
    """

    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                f"Database not found: {DB_PATH}. "
                "Put SecureFlow-AI5.db in the same folder as main.py."
            )
        )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    con = get_db()

    try:

        cur = con.cursor()

        # ----------------------------------------------------
        # Dynamic challenge table
        # ----------------------------------------------------

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS challenge_sessions (

                challenge_id TEXT PRIMARY KEY,

                user_id TEXT NOT NULL,

                recipient_id TEXT NOT NULL,

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

        con.commit()

    finally:

        con.close()


@app.on_event("startup")
def startup():

    initialize_database()


# ============================================================
# MODELS
# ============================================================

class AnalyzePayment(BaseModel):

    # Payer MUST come from database
    payer_id: str

    # Recipient can be ANYTHING entered by the judge
    recipient_name: str
    recipient_upi_id: str

    amount: float = Field(gt=0)

    # --------------------------------------------------------
    # FINAL RISK ENGINE
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
        "risk_scale": "0-100",
        "thresholds": {
            "pay": "0-44",
            "hold": "45-69",
            "block": "70-100"
        }
    }


@app.get("/health")
def health():

    con = get_db()

    try:

        con.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected"
        }

    finally:

        con.close()


# ============================================================
# DATABASE INFORMATION
# ============================================================

@app.get("/database-info")
def database_info():

    con = get_db()

    try:

        users_count = con.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0]

        recipients_count = con.execute(
            "SELECT COUNT(*) FROM recipients"
        ).fetchone()[0]

        transactions_count = con.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        return {
            "database": DB_PATH.name,
            "connected": True,
            "users": users_count,
            "recipients": recipients_count,
            "transactions": transactions_count
        }

    finally:

        con.close()


# ============================================================
# CURRENT BALANCE
#
# IMPORTANT:
#
# The actual database contains:
#
# initial_bank_balance
#
# We calculate live balance as:
#
# initial balance - SUCCESS transactions
#
# This means we don't need to modify your original users table.
# ============================================================

def calculate_current_balance(
    con,
    user_id
):

    row = con.execute(
        """
        SELECT
            initial_bank_balance

        FROM users

        WHERE user_id = ?

        LIMIT 1
        """,
        (user_id,)
    ).fetchone()

    if not row:
        return None

    initial_balance = float(
        row["initial_bank_balance"] or 0
    )

    spent_row = con.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS total_spent

        FROM transactions

        WHERE user_id = ?

        AND UPPER(
            TRIM(transaction_status)
        ) = 'SUCCESS'
        """,
        (user_id,)
    ).fetchone()

    total_spent = float(
        spent_row["total_spent"] or 0
    )

    current_balance = (
        initial_balance -
        total_spent
    )

    return max(
        0,
        round(current_balance, 2)
    )


# ============================================================
# GET PAYERS
# ============================================================

@app.get("/users")
def get_users():

    con = get_db()

    try:

        rows = con.execute(
            """
            SELECT
                user_id,
                name,
                living_area,
                common_location,
                known_device,
                initial_bank_balance,
                average_transaction,
                total_transactions

            FROM users

            ORDER BY name
            """
        ).fetchall()

        users = []

        for row in rows:

            user = dict(row)

            user["current_balance"] = (
                calculate_current_balance(
                    con,
                    row["user_id"]
                )
            )

            users.append(user)

        return {
            "users": users
        }

    finally:

        con.close()


# ============================================================
# GET CURRENT BALANCE
# ============================================================

@app.get("/balance/{user_id}")
def get_balance(user_id: str):

    con = get_db()

    try:

        payer = find_payer(
            con,
            user_id
        )

        if not payer:

            raise HTTPException(
                status_code=404,
                detail="Payer not found."
            )

        balance = calculate_current_balance(
            con,
            user_id
        )

        return {
            "user_id": user_id,
            "name": payer["name"],
            "balance": balance
        }

    finally:

        con.close()


# ============================================================
# GET RECIPIENTS
#
# This is ONLY for optional quick selection.
#
# A judge can still enter ANY recipient manually.
# ============================================================

@app.get("/recipients")
def get_recipients():

    con = get_db()

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
            "recipients": [
                dict(row)
                for row in rows
            ]
        }

    finally:

        con.close()


# ============================================================
# FIND PAYER
# ============================================================

def find_payer(
    con,
    payer_id
):

    return con.execute(
        """
        SELECT *

        FROM users

        WHERE user_id = ?

        LIMIT 1
        """,
        (payer_id,)
    ).fetchone()


# ============================================================
# FIND EXISTING RECIPIENT
# ============================================================

def find_recipient(
    con,
    recipient_name,
    recipient_upi_id
):

    return con.execute(
        """
        SELECT *

        FROM recipients

        WHERE
            LOWER(TRIM(upi_id))
            =
            LOWER(TRIM(?))

        OR
            LOWER(TRIM(recipient_name))
            =
            LOWER(TRIM(?))

        LIMIT 1
        """,
        (
            recipient_upi_id,
            recipient_name
        )
    ).fetchone()


# ============================================================
# ENSURE RECIPIENT
#
# Recipient can be entered manually.
#
# If it already exists -> use it.
#
# If it doesn't exist -> create a minimal recipient record.
#
# The judge therefore NEVER needs the recipient to already
# exist in the database.
# ============================================================

def ensure_recipient(
    con,
    recipient_name,
    recipient_upi_id
):

    existing = find_recipient(
        con,
        recipient_name,
        recipient_upi_id
    )

    if existing:

        return existing

    recipient_id = (
        "R-" +
        uuid.uuid4().hex[:10].upper()
    )

    con.execute(
        """
        INSERT INTO recipients (

            recipient_id,
            recipient_name,
            upi_id,
            recipient_device_name,
            recipient_location,
            recipient_type

        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            recipient_id,
            recipient_name.strip(),
            recipient_upi_id.strip(),
            "UNKNOWN",
            "UNKNOWN",
            "Unknown"
        )
    )

    return con.execute(
        """
        SELECT *

        FROM recipients

        WHERE recipient_id = ?

        LIMIT 1
        """,
        (recipient_id,)
    ).fetchone()


# ============================================================
# RELATIONSHIP
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

        WHERE
            user_id = ?

        AND
            recipient_id = ?

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

        WHERE
            user_id = ?

        AND
            recipient_id = ?

        ORDER BY
            transaction_time DESC
        """,
        (
            user_id,
            recipient_id
        )
    ).fetchall()


# ============================================================
# AMOUNT RISK
#
# Amount deviation is NOT a checkbox.
#
# AI/backend automatically evaluates it.
#
# Maximum = 9 points.
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

        if str(
            row["transaction_status"]
        ).upper() == "SUCCESS"

    ]

    if historical_amounts:

        typical_amount = (
            sum(historical_amounts)
            /
            len(historical_amounts)
        )

    else:

        typical_amount = float(
            payer["average_transaction"] or 0
        )

    if typical_amount <= 0:

        return 0, 0

    ratio = (
        amount /
        typical_amount
    )

    if ratio <= 1.5:
        score = 0

    elif ratio <= 2.0:
        score = 3

    elif ratio <= 2.5:
        score = 5

    elif ratio <= 3.0:
        score = 7

    else:
        score = 9

    return score, typical_amount


# ============================================================
# DYNAMIC QUESTION GENERATOR
#
# Questions are based on actual payer information in DB.
# ============================================================

def generate_dynamic_question(
    con,
    payer,
    recipient,
    relationship
):

    candidates = []

    # --------------------------------------------------------
    # Payer's college
    # --------------------------------------------------------

    if payer["college_name"]:

        candidates.append(
            {
                "question":
                    "What college is registered "
                    "on your SecureFlow profile?",

                "answer":
                    str(
                        payer["college_name"]
                    )
            }
        )

    # --------------------------------------------------------
    # Payer's living area
    # --------------------------------------------------------

    if payer["living_area"]:

        candidates.append(
            {
                "question":
                    "What is the living area "
                    "registered on your profile?",

                "answer":
                    str(
                        payer["living_area"]
                    )
            }
        )

    # --------------------------------------------------------
    # Common location
    # --------------------------------------------------------

    if payer["common_location"]:

        candidates.append(
            {
                "question":
                    "What is your usual payment location?",

                "answer":
                    str(
                        payer["common_location"]
                    )
            }
        )

    # --------------------------------------------------------
    # Known device
    # --------------------------------------------------------

    if payer["known_device"]:

        candidates.append(
            {
                "question":
                    "What device is normally "
                    "registered to your account?",

                "answer":
                    str(
                        payer["known_device"]
                    )
            }
        )

    # --------------------------------------------------------
    # Recipient relationship
    # --------------------------------------------------------

    if relationship:

        previous_connection = bool(
            relationship["previous_connection"]
        )

        count = int(
            relationship[
                "previous_transaction_count"
            ] or 0
        )

        if previous_connection:

            candidates.append(
                {
                    "question":
                        f"Have you previously paid "
                        f"{recipient['recipient_name']}?",

                    "answer":
                        "yes"
                }
            )

            candidates.append(
                {
                    "question":
                        f"Approximately how many previous "
                        f"payments have you made to "
                        f"{recipient['recipient_name']}?",

                    "answer":
                        str(count)
                }
            )

            if relationship["connection_type"]:

                candidates.append(
                    {
                        "question":
                            f"What is the relationship type "
                            f"you have with "
                            f"{recipient['recipient_name']}?",

                        "answer":
                            str(
                                relationship[
                                    "connection_type"
                                ]
                            )
                    }
                )

        else:

            candidates.append(
                {
                    "question":
                        f"Have you previously paid "
                        f"{recipient['recipient_name']}?",

                    "answer":
                        "no"
                }
            )

    # --------------------------------------------------------
    # Recipient information, ONLY if recipient exists in DB
    # --------------------------------------------------------

    if recipient:

        if recipient["recipient_location"]:

            candidates.append(
                {
                    "question":
                        f"What location is associated "
                        f"with {recipient['recipient_name']}?",

                    "answer":
                        str(
                            recipient[
                                "recipient_location"
                            ]
                        )
                }
            )

        if recipient["recipient_type"]:

            candidates.append(
                {
                    "question":
                        f"What type of recipient is "
                        f"{recipient['recipient_name']} "
                        f"according to the profile?",

                    "answer":
                        str(
                            recipient[
                                "recipient_type"
                            ]
                        )
                }
            )

    # --------------------------------------------------------
    # If possible, use transaction history to make question
    # --------------------------------------------------------

    if recipient:

        history = get_transaction_history(
            con,
            payer["user_id"],
            recipient["recipient_id"]
        )

        successful_amounts = [

            float(row["amount"])

            for row in history

            if str(
                row["transaction_status"]
            ).upper() == "SUCCESS"

        ]

        if successful_amounts:

            average = (
                sum(successful_amounts)
                /
                len(successful_amounts)
            )

            candidates.append(
                {
                    "question":
                        f"Approximately how much do you "
                        f"usually send to "
                        f"{recipient['recipient_name']}?",

                    "answer":
                        str(round(average))
                }
            )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    unique = []

    seen = set()

    for item in candidates:

        key = (
            item["question"],
            item["answer"]
        )

        if key not in seen:

            seen.add(key)

            unique.append(item)

    # --------------------------------------------------------
    # Random dynamic question
    # --------------------------------------------------------

    if not unique:

        return {

            "question":
                "What is your registered payer name?",

            "answer":
                str(payer["name"])

        }

    return random.choice(unique)


# ============================================================
# ANSWER NORMALIZATION
# ============================================================

def normalize_answer(value):

    return (
        str(value)
        .strip()
        .lower()
    )


# ============================================================
# ANSWER CHECK
# ============================================================

def answer_is_correct(
    user_answer,
    expected_answer
):

    user = normalize_answer(
        user_answer
    )

    expected = normalize_answer(
        expected_answer
    )

    # Exact
    if user == expected:

        return True

    # Yes/no variations
    yes_values = {
        "yes",
        "y",
        "yeah",
        "yep",
        "correct"
    }

    no_values = {
        "no",
        "n",
        "nope"
    }

    if expected == "yes" and user in yes_values:
        return True

    if expected == "no" and user in no_values:
        return True

    # Numeric tolerance
    try:

        user_number = float(user)
        expected_number = float(expected)

        tolerance = max(
            100,
            expected_number * 0.15
        )

        if abs(
            user_number - expected_number
        ) <= tolerance:

            return True

    except ValueError:

        pass

    # Text containment
    if (
        len(expected) >= 3
        and (
            expected in user
            or user in expected
        )
    ):

        return True

    return False


# ============================================================
# INSERT TRANSACTION
# ============================================================

def insert_transaction(
    con,
    transaction_id,
    payer,
    recipient,
    amount,
    status,
    relationship=None
):

    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    previous_connection = 0

    if relationship:

        previous_connection = int(
            bool(
                relationship[
                    "previous_connection"
                ]
            )
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
            recipient["recipient_id"],
            amount,
            now,
            payer["known_device"],
            recipient["recipient_device_name"],
            payer["common_location"],
            payer["common_location"],
            previous_connection,
            status,
            now
        )
    )


# ============================================================
# ANALYZE + PAY
# ============================================================

@app.post("/analyze-payment")
def analyze_payment(
    payment: AnalyzePayment
):

    con = get_db()

    try:

        # ====================================================
        # PAYER
        # ====================================================

        payer = find_payer(
            con,
            payment.payer_id
        )

        if not payer:

            raise HTTPException(
                status_code=404,
                detail="Selected payer does not exist."
            )

        # ====================================================
        # RECIPIENT
        #
        # Can be ANYTHING entered by judge.
        # ====================================================

        recipient = ensure_recipient(
            con,
            payment.recipient_name,
            payment.recipient_upi_id
        )

        # ====================================================
        # LIVE BALANCE
        # ====================================================

        current_balance = (
            calculate_current_balance(
                con,
                payer["user_id"]
            )
        )

        # ====================================================
        # BALANCE CHECK
        # ====================================================

        if payment.amount > current_balance:

            return {
                "status": "FAILED",
                "decision": "INSUFFICIENT_BALANCE",
                "risk_score": 0,
                "balance": current_balance,
                "message":
                    "Payment failed because the payer "
                    "does not have sufficient balance."
            }

        # ====================================================
        # RELATIONSHIP
        # ====================================================

        relationship = get_relationship(
            con,
            payer["user_id"],
            recipient["recipient_id"]
        )

        # ====================================================
        # AMOUNT RISK
        # ====================================================

        amount_risk, typical_amount = (
            calculate_amount_risk(
                con,
                payer,
                recipient["recipient_id"],
                payment.amount
            )
        )

        # ====================================================
        # RISK SIGNALS
        # ====================================================

        signals = []

        # ----------------------------------------------------
        # Amount
        # ----------------------------------------------------

        if amount_risk > 0:

            signals.append(
                {
                    "name":
                        "Amount deviation",

                    "score":
                        amount_risk
                }
            )

        # ----------------------------------------------------
        # New beneficiary +15
        # ----------------------------------------------------

        is_new_beneficiary = (
            payment.new_beneficiary
        )

        if relationship:

            if not bool(
                relationship[
                    "previous_connection"
                ]
            ):

                is_new_beneficiary = True

        add_signal(
            signals,
            "New beneficiary",
            15,
            is_new_beneficiary
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
        # Velocity +10
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
        # TOTAL
        # ====================================================

        risk_score = sum(
            signal["score"]
            for signal in signals
        )

        # Keep it within the displayed 0-100 scale.
        risk_score = max(
            0,
            min(
                100,
                risk_score
            )
        )

        # ====================================================
        # TRANSACTION ID
        # ====================================================

        transaction_id = (
            "T-" +
            uuid.uuid4().hex[:10].upper()
        )

        # ====================================================
        # 70+ = BLOCK IMMEDIATELY
        # ====================================================

        if risk_score >= 70:

            insert_transaction(
                con,
                transaction_id,
                payer,
                recipient,
                payment.amount,
                "BLOCKED",
                relationship
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
                    "the risk score is 70 or above.",
                "balance": current_balance
            }

        # ====================================================
        # 0-44 = SUCCESS
        # ====================================================

        if risk_score <= 44:

            insert_transaction(
                con,
                transaction_id,
                payer,
                recipient,
                payment.amount,
                "SUCCESS",
                relationship
            )

            con.commit()

            new_balance = (
                calculate_current_balance(
                    con,
                    payer["user_id"]
                )
            )

            return {
                "status": "SUCCESS",
                "decision": "PAY",
                "transaction_id": transaction_id,
                "risk_score": risk_score,
                "signals": signals,
                "previous_balance": current_balance,
                "new_balance": new_balance,
                "message":
                    "Payment completed successfully."
            }

        # ====================================================
        # 45-69 = HOLD
        # ====================================================

        dynamic_question = (
            generate_dynamic_question(
                con,
                payer,
                recipient,
                relationship
            )
        )

        challenge_id = (
            "CH-" +
            uuid.uuid4().hex[:12].upper()
        )

        now = datetime.now()

        created_at = now.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        expires_at = (
            now +
            timedelta(minutes=5)
        ).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # ----------------------------------------------------
        # Store expected answer SERVER SIDE.
        # The frontend never receives it.
        # ----------------------------------------------------

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
                dynamic_question["question"],
                dynamic_question["answer"],
                created_at,
                expires_at,
                "PENDING"
            )
        )

        con.commit()

        # IMPORTANT:
        # No balance deduction happens here.

        return {
            "status": "HELD",
            "decision": "HOLD",
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "signals": signals,
            "challenge": {
                "challenge_id":
                    challenge_id,

                "question":
                    dynamic_question["question"],

                "expires_in_seconds":
                    300
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

    con = get_db()

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
                detail=
                    "Verification challenge not found."
            )

        # ====================================================
        # CHECK STATUS
        # ====================================================

        if challenge["status"] != "PENDING":

            return {
                "status": "FAILED",
                "decision": "CANCEL",
                "risk_score":
                    challenge["risk_score"],
                "message":
                    "This verification challenge "
                    "is no longer active."
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
                "risk_score":
                    challenge["risk_score"],
                "message":
                    "Verification expired. "
                    "Payment cancelled."
            }

        # ====================================================
        # VERIFY ANSWER
        # ====================================================

        correct = answer_is_correct(
            verification.answer,
            challenge["expected_answer"]
        )

        # ====================================================
        # WRONG ANSWER
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

            payer = find_payer(
                con,
                challenge["user_id"]
            )

            recipient = con.execute(
                """
                SELECT *

                FROM recipients

                WHERE recipient_id = ?

                LIMIT 1
                """,
                (
                    challenge["recipient_id"]
                )
            ).fetchone()

            relationship = get_relationship(
                con,
                challenge["user_id"],
                challenge["recipient_id"]
            )

            transaction_id = (
                "T-" +
                uuid.uuid4().hex[:10].upper()
            )

            insert_transaction(
                con,
                transaction_id,
                payer,
                recipient,
                challenge["transaction_amount"],
                "CANCELLED",
                relationship
            )

            con.commit()

            current_balance = (
                calculate_current_balance(
                    con,
                    challenge["user_id"]
                )
            )

            return {
                "status": "FAILED",
                "decision": "CANCEL",
                "risk_score":
                    challenge["risk_score"],
                "transaction_id":
                    transaction_id,
                "new_balance":
                    current_balance,
                "message":
                    "Verification answer was incorrect. "
                    "Payment cancelled immediately."
            }

        # ====================================================
        # CORRECT ANSWER
        # ====================================================

        payer = find_payer(
            con,
            challenge["user_id"]
        )

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

            LIMIT 1
            """,
            (
                challenge["recipient_id"]
            )
        ).fetchone()

        if not recipient:

            raise HTTPException(
                status_code=404,
                detail="Recipient record not found."
            )

        # ====================================================
        # GET FRESH BALANCE
        # ====================================================

        current_balance = (
            calculate_current_balance(
                con,
                challenge["user_id"]
            )
        )

        payment_amount = float(
            challenge["transaction_amount"]
        )

        # ====================================================
        # BALANCE CHECK AGAIN
        # ====================================================

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
                "risk_score":
                    challenge["risk_score"],
                "message":
                    "Payment cancelled because the payer "
                    "no longer has sufficient balance."
            }

        # ====================================================
        # MARK VERIFIED
        # ====================================================

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

        # ====================================================
        # RECORD SUCCESS
        #
        # This is what effectively deducts the money because
        # current balance = initial balance - SUCCESS total.
        # ====================================================

        transaction_id = (
            "T-" +
            uuid.uuid4().hex[:10].upper()
        )

        relationship = get_relationship(
            con,
            challenge["user_id"],
            challenge["recipient_id"]
        )

        insert_transaction(
            con,
            transaction_id,
            payer,
            recipient,
            payment_amount,
            "SUCCESS",
            relationship
        )

        con.commit()

        # ====================================================
        # NEW BALANCE
        # ====================================================

        new_balance = (
            calculate_current_balance(
                con,
                challenge["user_id"]
            )
        )

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
                "Verification successful. "
                "Payment completed."
        }

    finally:

        con.close()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.get("/transactions/{user_id}")
def get_transactions(user_id: str):

    con = get_db()

    try:

        rows = con.execute(
            """
            SELECT

                t.transaction_id,

                t.amount,

                t.transaction_time,

                t.transaction_status,

                t.payment_location,

                r.recipient_name,

                r.upi_id

            FROM transactions t

            LEFT JOIN recipients r

                ON t.recipient_id =
                   r.recipient_id

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
                [
                    dict(row)
                    for row in rows
                ]
        }

    finally:

        con.close()


# ============================================================
# ADD SIGNAL
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
# RUN
#
# Start with:
#
# python -m uvicorn main:app --reload
#
# ============================================================
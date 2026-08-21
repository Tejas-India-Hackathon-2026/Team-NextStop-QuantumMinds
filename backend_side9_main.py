from __future__ import annotations

import random
import secrets
import sqlite3
import statistics
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# SECUREFLOW-AI BACKEND
# ============================================================
#
# Put this file beside:
#
#     SecureFlow-AI8.db
#
# Install:
#
#     pip install fastapi uvicorn
#
# Run:
#
#     python backend.py
#
# Backend:
#
#     http://127.0.0.1:8000
#
# Swagger:
#
#     http://127.0.0.1:8000/docs
#
# ============================================================


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "SecureFlow-AI8.db"


# ============================================================
# FOUR PAYERS
# ============================================================

INITIAL_BALANCES = {
    "U002": 60000.0,   # Shubham Paul
    "U003": 50000.0,   # Shubham Mukherjee
    "U004": 40000.0,   # Tridip Debroy
    "U001": 55000.0,   # Soumadip Das
}


USERS = {

    "U001": {
        "name": "Soumadip Das",
        "date_of_birth": "2005-04-18",
        "college_name": "Haldia Institute of Technology",
        "living_area": "Haldia",
        "known_device": "Samsung Galaxy S23 - SOUMADIP",
        "common_location": "Haldia",
    },

    "U002": {
        "name": "Shubham Paul",
        "date_of_birth": "2004-11-07",
        "college_name": "Haldia Institute of Technology",
        "living_area": "Haldia",
        "known_device": "OnePlus 12R - SHUBHAM",
        "common_location": "Kolkata",
    },

    "U003": {
        "name": "Shubham Mukherjee",
        "date_of_birth": "2005-02-21",
        "college_name": "Haldia Institute of Technology",
        "living_area": "Haldia",
        "known_device": "Redmi Note 13 Pro - MUKHERJEE",
        "common_location": "Haldia",
    },

    "U004": {
        "name": "Tridip Debroy",
        "date_of_birth": "2004-08-13",
        "college_name": "Haldia Institute of Technology",
        "living_area": "Haldia",
        "known_device": "Google Pixel 8 - TRIDIP",
        "common_location": "Kolkata",
    },
}


# ============================================================
# EIGHT RISK SWITCHES
# ============================================================
#
# These are the ONLY eight user-controlled risk factors.
#
# Change True -> False if you want to disable a factor
# from the backend.
#
# AMOUNT IS INTENTIONALLY NOT HERE.
# Amount deviation is calculated automatically.
# ============================================================

SIGNAL_SWITCHES = {

    "time_anomaly": True,             # 7
    "transaction_frequency": True,    # 12
    "new_device": True,               # 15
    "unusual_location": True,         # 15
    "sudden_location_change": True,   # 6
    "unknown_beneficiary": True,      # 12
    "previous_transaction": True,     # 13
    "typical_amount": True,           # 10

}


SIGNAL_WEIGHTS = {

    "time_anomaly": 7,
    "transaction_frequency": 12,
    "new_device": 15,
    "unusual_location": 15,
    "sudden_location_change": 6,
    "unknown_beneficiary": 12,
    "previous_transaction": 13,
    "typical_amount": 10,

}


SIGNAL_LABELS = {

    "time_anomaly": "Time anomaly",
    "transaction_frequency": "Transaction frequency",
    "new_device": "New device",
    "unusual_location": "Unusual location",
    "sudden_location_change": "Sudden location change",
    "unknown_beneficiary": "Unknown beneficiary",
    "previous_transaction": "Previous transaction",
    "typical_amount": "Typical amount",

}


# ============================================================
# FINAL DECISION THRESHOLDS
# ============================================================

LOW_MAX = 49

HOLD_MIN = 50
HOLD_MAX = 79

BLOCK_MIN = 80


# ============================================================
# DYNAMIC QUESTIONS
# ============================================================
#
# These are taken from the supplied screenshots.
#
# The screenshot clearly shows:
#
# DEVICE_CONFIRM
# AREA_CONFIRM
# LOCATION_CONFIRM
# DOB_CONFIRM
# COLLEGE_CONFIRM
# NEARBY_PLACE_CONFIRM
#
# The screenshot also shows AMOUNT_CONFIRM,
# HISTORY_CONFIRM and RECIPIENT_CONFIRM, but the question
# text itself is visibly truncated in the supplied image.
#
# Therefore this backend does NOT invent the missing text.
#
# ============================================================


QUESTION_BANK = {

    "U001": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for...",
            "expected_answer": "Samsung Galaxy S23 - SOUMADIP",
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "expected_answer": "Haldia",
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "expected_answer": "Haldia",
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "expected_answer": "2005-04-18",
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "expected_answer": "Haldia Institute of Technology",
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near...",
            "expected_answer": "Haldia Railway Station",
        },

    ],


    "U002": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for...",
            "expected_answer": "OnePlus 12R - SHUBHAM",
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "expected_answer": "Haldia",
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "expected_answer": "Kolkata",
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "expected_answer": "2004-11-07",
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "expected_answer": "Haldia Institute of Technology",
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near...",
            "expected_answer": "Haldia Township",
        },

    ],


    "U003": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for...",
            "expected_answer": "Redmi Note 13 Pro - MUKHERJEE",
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "expected_answer": "Haldia",
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "expected_answer": "Haldia",
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "expected_answer": "2005-02-21",
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "expected_answer": "Haldia Institute of Technology",
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near...",
            "expected_answer": "Haldia Dock Complex",
        },

    ],


    "U004": [

        {
            "question_id": 5,
            "code": "DEVICE_CONFIRM",
            "question": "Which device do you normally use for...",
            "expected_answer": "Google Pixel 8 - TRIDIP",
        },

        {
            "question_id": 3,
            "code": "AREA_CONFIRM",
            "question": "Which area do you live in?",
            "expected_answer": "Haldia",
        },

        {
            "question_id": 6,
            "code": "LOCATION_CONFIRM",
            "question": "What is your usual payment location?",
            "expected_answer": "Kolkata",
        },

        {
            "question_id": 1,
            "code": "DOB_CONFIRM",
            "question": "What is your date of birth?",
            "expected_answer": "2004-08-13",
        },

        {
            "question_id": 2,
            "code": "COLLEGE_CONFIRM",
            "question": "What is the name of your college?",
            "expected_answer": "Haldia Institute of Technology",
        },

        {
            "question_id": 4,
            "code": "NEARBY_PLACE_CONFIRM",
            "question": "Tell us one well-known place near...",
            "expected_answer": "Haldia Township",
        },

    ],

}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:

    alphabet = string.ascii_uppercase + string.digits

    token = "".join(
        secrets.choice(alphabet)
        for _ in range(12)
    )

    return f"{prefix}-{token}"


def normalize_answer(value: str) -> str:

    value = str(value or "").strip().casefold()

    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = " ".join(value.split())

    return value


def answers_match(given: str, expected: str) -> bool:

    a = normalize_answer(given)
    b = normalize_answer(expected)

    if a == b:
        return True

    a2 = a.replace("/", "-").replace(".", "-")
    b2 = b.replace("/", "-").replace(".", "-")

    return a2 == b2


# ============================================================
# DATABASE
# ============================================================


def get_connection() -> sqlite3.Connection:

    con = sqlite3.connect(
        DB_PATH,
        timeout=20,
    )

    con.row_factory = sqlite3.Row

    con.execute(
        "PRAGMA foreign_keys = ON"
    )

    con.execute(
        "PRAGMA busy_timeout = 20000"
    )

    return con


def ensure_column(
    con: sqlite3.Connection,
    table: str,
    column: str,
    definition: str,
) -> None:

    existing = {

        row["name"]

        for row in con.execute(
            f'PRAGMA table_info("{table}")'
        ).fetchall()

    }

    if column not in existing:

        con.execute(
            f'ALTER TABLE "{table}" '
            f'ADD COLUMN "{column}" {definition}'
        )


def init_db() -> None:

    con = get_connection()

    try:

        con.executescript(
            """

            CREATE TABLE IF NOT EXISTS users (

                user_id TEXT PRIMARY KEY,

                name TEXT NOT NULL,

                date_of_birth TEXT,

                college_name TEXT,

                living_area TEXT,

                known_device TEXT,

                common_location TEXT,

                initial_bank_balance REAL DEFAULT 0,

                current_bank_balance REAL DEFAULT 0,

                average_transaction REAL DEFAULT 0,

                total_transactions INTEGER DEFAULT 0,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP

            );


            CREATE TABLE IF NOT EXISTS transactions (

                transaction_id TEXT PRIMARY KEY,

                user_id TEXT NOT NULL,

                recipient_id TEXT,

                amount REAL NOT NULL,

                transaction_time TEXT,

                sender_device_name TEXT,

                recipient_device_name TEXT,

                payment_location TEXT,

                previous_location TEXT,

                previous_connection INTEGER DEFAULT 0,

                transaction_status TEXT DEFAULT 'SUCCESS',

                risk_score INTEGER,

                risk_decision TEXT DEFAULT 'ALLOW',

                recipient_name TEXT,

                recipient_upi_id TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP

            );


            CREATE TABLE IF NOT EXISTS challenge_sessions (

                challenge_id TEXT PRIMARY KEY,

                user_id TEXT NOT NULL,

                recipient_id TEXT,

                recipient_name TEXT,

                recipient_upi_id TEXT,

                amount REAL NOT NULL,

                risk_score INTEGER NOT NULL,

                question_id INTEGER NOT NULL,

                question_code TEXT,

                question_text TEXT NOT NULL,

                expected_answer TEXT NOT NULL,

                created_at TEXT NOT NULL,

                expires_at TEXT NOT NULL,

                status TEXT DEFAULT 'PENDING',

                transaction_id TEXT

            );

            """
        )


        # ----------------------------------------------------
        # Compatibility with older SecureFlow-AI databases
        # ----------------------------------------------------

        user_columns = {

            "date_of_birth": "TEXT",

            "college_name": "TEXT",

            "living_area": "TEXT",

            "known_device": "TEXT",

            "common_location": "TEXT",

            "initial_bank_balance": "REAL DEFAULT 0",

            "current_bank_balance": "REAL DEFAULT 0",

            "average_transaction": "REAL DEFAULT 0",

            "total_transactions": "INTEGER DEFAULT 0",

            "created_at": "TEXT",

        }


        for col, definition in user_columns.items():

            ensure_column(
                con,
                "users",
                col,
                definition,
            )


        tx_columns = {

            "recipient_id": "TEXT",

            "amount": "REAL",

            "transaction_time": "TEXT",

            "sender_device_name": "TEXT",

            "recipient_device_name": "TEXT",

            "payment_location": "TEXT",

            "previous_location": "TEXT",

            "previous_connection": "INTEGER DEFAULT 0",

            "transaction_status": "TEXT DEFAULT 'SUCCESS'",

            "risk_score": "INTEGER",

            "risk_decision": "TEXT DEFAULT 'ALLOW'",

            "recipient_name": "TEXT",

            "recipient_upi_id": "TEXT",

            "created_at": "TEXT",

        }


        for col, definition in tx_columns.items():

            ensure_column(
                con,
                "transactions",
                col,
                definition,
            )


        # ----------------------------------------------------
        # Create / synchronize the four demo payers
        # ----------------------------------------------------

        for user_id, data in USERS.items():

            existing = con.execute(

                """
                SELECT user_id
                FROM users
                WHERE user_id = ?

                """,

                (user_id,),

            ).fetchone()


            if existing is None:

                balance = INITIAL_BALANCES[user_id]

                con.execute(

                    """

                    INSERT INTO users (

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

                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?)

                    """,

                    (

                        user_id,

                        data["name"],

                        data["date_of_birth"],

                        data["college_name"],

                        data["living_area"],

                        data["known_device"],

                        data["common_location"],

                        balance,

                        balance,

                        iso_now(),

                    ),

                )


            else:

                con.execute(

                    """

                    UPDATE users

                    SET

                        name = ?,

                        date_of_birth = ?,

                        college_name = ?,

                        living_area = ?,

                        known_device = ?,

                        common_location = ?

                    WHERE user_id = ?

                    """,

                    (

                        data["name"],

                        data["date_of_birth"],

                        data["college_name"],

                        data["living_area"],

                        data["known_device"],

                        data["common_location"],

                        user_id,

                    ),

                )


        con.commit()

    finally:

        con.close()


# ============================================================
# USER FUNCTIONS
# ============================================================


def user_row(
    user_id: str,
) -> sqlite3.Row | None:

    con = get_connection()

    try:

        return con.execute(

            """

            SELECT *

            FROM users

            WHERE user_id = ?

            """,

            (user_id,),

        ).fetchone()

    finally:

        con.close()


def user_dict(
    row: sqlite3.Row,
) -> dict[str, Any]:

    return {

        "user_id": row["user_id"],

        "name": row["name"],

        "date_of_birth": row["date_of_birth"],

        "college_name": row["college_name"],

        "living_area": row["living_area"],

        "known_device": row["known_device"],

        "common_location": row["common_location"],

        "initial_bank_balance": float(
            row["initial_bank_balance"] or 0
        ),

        "current_bank_balance": float(
            row["current_bank_balance"] or 0
        ),

        "average_transaction": float(
            row["average_transaction"] or 0
        ),

        "total_transactions": int(
            row["total_transactions"] or 0
        ),

    }


# ============================================================
# HISTORICAL TRANSACTION PATTERN
# ============================================================


def successful_history(
    user_id: str,
) -> list[float]:

    con = get_connection()

    try:

        rows = con.execute(

            """

            SELECT amount

            FROM transactions

            WHERE user_id = ?

              AND UPPER(
                    COALESCE(transaction_status, '')
                  ) = 'SUCCESS'

              AND amount > 0

            ORDER BY created_at ASC

            """,

            (user_id,),

        ).fetchall()

        return [

            float(row["amount"])

            for row in rows

        ]

    finally:

        con.close()


# ============================================================
# AUTOMATIC AMOUNT DEVIATION
# ============================================================
#
# IMPORTANT:
#
# Amount is NOT a checkbox.
#
# <= ₹1000:
#     amount risk = 0
#
# > ₹1000:
#     compare against the payer's historical successful
#     transaction pattern.
#
# Maximum automatic amount contribution = 10.
# ============================================================


def amount_deviation_score(
    user_id: str,
    amount: float,
) -> tuple[int, str]:

    if amount <= 1000:

        return (
            0,
            "Amount <= ₹1,000: no amount anomaly.",
        )


    history = successful_history(user_id)


    if not history:

        return (
            0,
            "No previous successful transaction pattern available.",
        )


    median = statistics.median(history)


    if median <= 0:

        return (
            0,
            "No valid historical baseline available.",
        )


    ratio = amount / median


    if ratio <= 1.5:

        score = 0

    elif ratio <= 2.0:

        score = 2

    elif ratio <= 3.0:

        score = 5

    elif ratio <= 4.0:

        score = 7

    else:

        score = 10


    reason = (

        f"Amount ₹{amount:,.2f} is "

        f"{ratio:.2f}× the payer's "

        f"historical median "

        f"₹{median:,.2f}."

    )


    return score, reason


# ============================================================
# RISK ENGINE
# ============================================================


def calculate_risk(
    payload: "PaymentRequest",
) -> tuple[
    int,
    list[dict[str, Any]],
    str,
]:

    total = 0

    rows = []


    # --------------------------------------------------------
    # Eight checkbox-controlled factors
    # --------------------------------------------------------

    for key, weight in SIGNAL_WEIGHTS.items():

        enabled = SIGNAL_SWITCHES.get(
            key,
            True,
        )

        selected = bool(
            getattr(
                payload,
                key,
                False,
            )
        )


        if enabled and selected:

            points = weight

            active = True

        else:

            points = 0

            active = False


        total += points


        rows.append(

            {

                "name": SIGNAL_LABELS[key],

                "key": key,

                "score": points,

                "active": active,

                "enabled": enabled,

                "weight": weight,

            }

        )


    # --------------------------------------------------------
    # Automatic amount deviation.
    #
    # NOT a checkbox.
    # --------------------------------------------------------

    amount_score, amount_reason = (
        amount_deviation_score(

            payload.payer_id,

            payload.amount,

        )
    )


    total += amount_score


    rows.append(

        {

            "name": "Automatic amount deviation",

            "key": "amount_deviation",

            "score": amount_score,

            "active": amount_score > 0,

            "enabled": True,

            "weight": 10,

            "automatic": True,

            "reason": amount_reason,

        }

    )


    total = max(
        0,
        min(
            100,
            int(total),
        ),
    )


    # --------------------------------------------------------
    # Final decision
    # --------------------------------------------------------

    if total >= BLOCK_MIN:

        decision = "BLOCK"

    elif total >= HOLD_MIN:

        decision = "HOLD"

    else:

        decision = "ALLOW"


    return (
        total,
        rows,
        decision,
    )


# ============================================================
# TRANSACTION CREATION
# ============================================================


def insert_transaction(
    con: sqlite3.Connection,
    *,
    user_id: str,
    recipient_name: str,
    recipient_upi_id: str,
    amount: float,
    status: str,
    risk_score: int,
    risk_decision: str,
    transaction_id: str | None = None,
) -> str:

    tx_id = (
        transaction_id
        or new_id("TXN")
    )

    now = iso_now()


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

            risk_score,

            risk_decision,

            recipient_name,

            recipient_upi_id,

            created_at

        )

        VALUES (

            ?, ?, ?, ?, ?, ?, ?, ?,

            ?, ?, ?, ?, ?, ?, ?, ?

        )

        """,

        (

            tx_id,

            user_id,

            recipient_upi_id,

            amount,

            now,

            None,

            None,

            None,

            None,

            0,

            status,

            risk_score,

            risk_decision,

            recipient_name,

            recipient_upi_id,

            now,

        ),

    )


    return tx_id


# ============================================================
# DYNAMIC QUESTION
# ============================================================


def choose_question(
    user_id: str,
) -> dict[str, Any]:

    questions = QUESTION_BANK.get(
        user_id,
        [],
    )


    if not questions:

        raise RuntimeError(
            "No source-backed verification "
            "questions exist for this payer."
        )


    return random.choice(questions)


def create_challenge(
    con: sqlite3.Connection,
    payload: "PaymentRequest",
    risk_score: int,
    transaction_id: str,
) -> dict[str, Any]:

    question = choose_question(
        payload.payer_id
    )


    challenge_id = new_id("CH")


    created = utc_now()


    expires = (
        created
        + timedelta(minutes=5)
    )


    con.execute(

        """

        INSERT INTO challenge_sessions (

            challenge_id,

            user_id,

            recipient_id,

            recipient_name,

            recipient_upi_id,

            amount,

            risk_score,

            question_id,

            question_code,

            question_text,

            expected_answer,

            created_at,

            expires_at,

            status,

            transaction_id

        )

        VALUES (

            ?, ?, ?, ?, ?, ?, ?, ?, ?,

            ?, ?, ?, ?, 'PENDING', ?

        )

        """,

        (

            challenge_id,

            payload.payer_id,

            payload.recipient_upi_id,

            payload.recipient_name,

            payload.recipient_upi_id,

            payload.amount,

            risk_score,

            question["question_id"],

            question["code"],

            question["question"],

            question["expected_answer"],

            created.isoformat(),

            expires.isoformat(),

            transaction_id,

        ),

    )


    return {

        "challenge_id": challenge_id,

        "question": question["question"],

        "question_code": question["code"],

        "expires_at": expires.isoformat(),

    }


# ============================================================
# REQUEST MODELS
# ============================================================


class PaymentRequest(BaseModel):

    payer_id: str

    recipient_name: str = Field(
        min_length=1,
        max_length=150,
    )

    recipient_upi_id: str = Field(
        min_length=3,
        max_length=200,
    )

    amount: float = Field(
        gt=0,
    )


    # EXACTLY 8 RISK CHECKBOXES

    time_anomaly: bool = False

    transaction_frequency: bool = False

    new_device: bool = False

    unusual_location: bool = False

    sudden_location_change: bool = False

    unknown_beneficiary: bool = False

    previous_transaction: bool = False

    typical_amount: bool = False


class ChallengeVerifyRequest(BaseModel):

    challenge_id: str = Field(
        min_length=3,
    )

    answer: str = Field(
        min_length=1,
        max_length=300,
    )


# ============================================================
# FASTAPI
# ============================================================


app = FastAPI(

    title="SecureFlow-AI Backend",

    version="1.0.0",

    description=(
        "Behavioural UPI transaction "
        "risk-analysis and verification backend."
    ),

)


# ------------------------------------------------------------
# CORS
# ------------------------------------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],

)


# ============================================================
# STARTUP
# ============================================================


@app.on_event("startup")
def startup():

    init_db()


# ============================================================
# BASIC ENDPOINTS
# ============================================================


@app.get("/")
def root():

    return {

        "service": "SecureFlow-AI",

        "status": "online",

        "database": str(DB_PATH),

        "question_source":
            "supplied screenshots only",

        "risk_thresholds": {

            "allow": "0-49",

            "hold": "50-79",

            "block": "80-100",

        },

    }


@app.get("/health")
def health():

    try:

        con = get_connection()

        try:

            con.execute(
                "SELECT 1"
            ).fetchone()

        finally:

            con.close()


        return {

            "status": "ok",

            "database": "connected",

            "database_path": str(
                DB_PATH
            ),

        }


    except Exception as exc:

        raise HTTPException(

            status_code=500,

            detail=str(exc),

        )


# ============================================================
# RISK CONFIG
# ============================================================


@app.get("/risk-config")
def risk_config():

    return {

        "switches": SIGNAL_SWITCHES,

        "weights": SIGNAL_WEIGHTS,

        "thresholds": {

            "allow_max": LOW_MAX,

            "hold_min": HOLD_MIN,

            "hold_max": HOLD_MAX,

            "block_min": BLOCK_MIN,

        },

        "amount_rule": {

            "under_or_equal_1000":
                "0 amount-anomaly points",

            "above_1000":
                "automatic comparison with payer history",

            "maximum_points":
                10,

        },

    }


# ============================================================
# USERS
# ============================================================


@app.get("/users")
def get_users():

    con = get_connection()

    try:

        rows = con.execute(

            """

            SELECT *

            FROM users

            WHERE user_id IN (

                'U001',

                'U002',

                'U003',

                'U004'

            )

            ORDER BY

                CASE user_id

                    WHEN 'U002' THEN 1

                    WHEN 'U003' THEN 2

                    WHEN 'U004' THEN 3

                    WHEN 'U001' THEN 4

                    ELSE 5

                END

            """

        ).fetchall()


        return {

            "users": [

                user_dict(row)

                for row in rows

            ]

        }


    finally:

        con.close()


@app.get("/users/{user_id}")
def get_user(
    user_id: str,
):

    row = user_row(
        user_id
    )


    if row is None:

        raise HTTPException(

            status_code=404,

            detail="Payer not found",

        )


    return {

        "user": user_dict(row)

    }


# ============================================================
# TRANSACTION HISTORY
# ============================================================


@app.get("/transactions/{user_id}")
def get_transactions(
    user_id: str,
):

    if user_row(user_id) is None:

        raise HTTPException(

            status_code=404,

            detail="Payer not found",

        )


    con = get_connection()

    try:

        rows = con.execute(

            """

            SELECT *

            FROM transactions

            WHERE user_id = ?

            ORDER BY

                datetime(created_at) DESC,

                rowid DESC

            LIMIT 100

            """,

            (user_id,),

        ).fetchall()


        return {

            "transactions": [

                dict(row)

                for row in rows

            ]

        }


    finally:

        con.close()


# ============================================================
# ANALYZE + PAY
# ============================================================


@app.post("/analyze-payment")
def analyze_payment(
    payload: PaymentRequest,
):

    # --------------------------------------------------------
    # Validate payer
    # --------------------------------------------------------

    row = user_row(
        payload.payer_id
    )


    if row is None:

        raise HTTPException(

            status_code=404,

            detail="Selected payer not found",

        )


    balance = float(
        row["current_bank_balance"]
        or 0
    )


    # --------------------------------------------------------
    # INSUFFICIENT BALANCE
    # --------------------------------------------------------

    if payload.amount > balance:

        return {

            "status":
                "INSUFFICIENT_BALANCE",

            "decision":
                "INSUFFICIENT_BALANCE",

            "message": (

                f"Insufficient balance. "

                f"Available balance is "

                f"₹{balance:,.2f}, "

                f"but the payment is "

                f"₹{payload.amount:,.2f}."

            ),

            "risk_score": None,

            "signals": [],

        }


    # --------------------------------------------------------
    # RISK ENGINE
    # --------------------------------------------------------

    (
        risk_score,
        signals,
        decision,
    ) = calculate_risk(
        payload
    )


    con = get_connection()

    try:

        # ----------------------------------------------------
        # SQLite atomic transaction
        # ----------------------------------------------------

        con.execute(
            "BEGIN IMMEDIATE"
        )


        # Re-read balance while locked.

        fresh = con.execute(

            """

            SELECT current_bank_balance

            FROM users

            WHERE user_id = ?

            """,

            (payload.payer_id,),

        ).fetchone()


        if fresh is None:

            con.rollback()

            raise HTTPException(

                status_code=404,

                detail="Payer not found",

            )


        fresh_balance = float(

            fresh["current_bank_balance"]

            or 0

        )


        # ----------------------------------------------------
        # Balance may have changed since initial check.
        # ----------------------------------------------------

        if payload.amount > fresh_balance:

            con.rollback()

            return {

                "status":
                    "INSUFFICIENT_BALANCE",

                "decision":
                    "INSUFFICIENT_BALANCE",

                "message": (

                    f"Insufficient balance. "

                    f"Available balance is "

                    f"₹{fresh_balance:,.2f}."

                ),

                "risk_score":
                    risk_score,

                "signals":
                    signals,

            }


        # ====================================================
        # HIGH RISK: BLOCK
        # ====================================================

        if decision == "BLOCK":

            tx_id = insert_transaction(

                con,

                user_id=payload.payer_id,

                recipient_name=
                    payload.recipient_name,

                recipient_upi_id=
                    payload.recipient_upi_id,

                amount=payload.amount,

                status="BLOCKED",

                risk_score=risk_score,

                risk_decision="BLOCK",

            )


            con.commit()


            return {

                "status": "BLOCKED",

                "decision": "BLOCK",

                "transaction_id": tx_id,

                "risk_score": risk_score,

                "signals": signals,

                "message": (

                    "Insecure transaction blocked. "

                    f"Risk score {risk_score}/100 "

                    "is at or above 80."

                ),

            }


        # ====================================================
        # MODERATE RISK: HOLD + QUESTION
        # ====================================================

        if decision == "HOLD":

            tx_id = insert_transaction(

                con,

                user_id=payload.payer_id,

                recipient_name=
                    payload.recipient_name,

                recipient_upi_id=
                    payload.recipient_upi_id,

                amount=payload.amount,

                status="HELD",

                risk_score=risk_score,

                risk_decision="HOLD",

            )


            challenge = create_challenge(

                con,

                payload,

                risk_score,

                tx_id,

            )


            con.commit()


            return {

                "status": "HELD",

                "decision": "HOLD",

                "transaction_id": tx_id,

                "risk_score": risk_score,

                "signals": signals,

                "challenge": challenge,

                "message": (

                    "Transaction temporarily held. "

                    "Answer the dynamic verification "

                    "question to release it."

                ),

            }


        # ====================================================
        # LOW RISK: SUCCESS
        # ====================================================

        tx_id = insert_transaction(

            con,

            user_id=payload.payer_id,

            recipient_name=
                payload.recipient_name,

            recipient_upi_id=
                payload.recipient_upi_id,

            amount=payload.amount,

            status="SUCCESS",

            risk_score=risk_score,

            risk_decision="ALLOW",

        )


        new_balance = (
            fresh_balance
            - payload.amount
        )


        # ----------------------------------------------------
        # Atomic balance deduction
        # ----------------------------------------------------

        updated = con.execute(

            """

            UPDATE users

            SET

                current_bank_balance = ?,

                total_transactions =

                    COALESCE(
                        total_transactions,
                        0
                    ) + 1

            WHERE

                user_id = ?

                AND current_bank_balance >= ?

            """,

            (

                new_balance,

                payload.payer_id,

                payload.amount,

            ),

        )


        if updated.rowcount != 1:

            con.rollback()

            return {

                "status":
                    "INSUFFICIENT_BALANCE",

                "decision":
                    "INSUFFICIENT_BALANCE",

                "message":
                    "Insufficient balance.",

                "risk_score":
                    risk_score,

                "signals":
                    signals,

            }


        # ----------------------------------------------------
        # Update historical average
        # ----------------------------------------------------

        avg = con.execute(

            """

            SELECT AVG(amount)
                AS avg_amount

            FROM transactions

            WHERE user_id = ?

              AND UPPER(
                    COALESCE(
                        transaction_status,
                        ''
                    )
                  ) = 'SUCCESS'

            """,

            (payload.payer_id,),

        ).fetchone()["avg_amount"]


        con.execute(

            """

            UPDATE users

            SET average_transaction = ?

            WHERE user_id = ?

            """,

            (

                float(avg or 0),

                payload.payer_id,

            ),

        )


        con.commit()


        return {

            "status": "SUCCESS",

            "decision": "ALLOW",

            "transaction_id": tx_id,

            "risk_score": risk_score,

            "signals": signals,

            "new_balance": new_balance,

            "message": (

                "Payment successful. "

                "Low-risk transaction approved."

            ),

        }


    except HTTPException:

        raise


    except Exception:

        con.rollback()

        raise


    finally:

        con.close()


# ============================================================
# VERIFY DYNAMIC QUESTION
# ============================================================


@app.post("/verify-challenge")
def verify_challenge(
    payload: ChallengeVerifyRequest,
):

    con = get_connection()

    try:

        # ----------------------------------------------------
        # Atomic challenge processing
        # ----------------------------------------------------

        con.execute(
            "BEGIN IMMEDIATE"
        )


        challenge = con.execute(

            """

            SELECT *

            FROM challenge_sessions

            WHERE challenge_id = ?

            """,

            (payload.challenge_id,),

        ).fetchone()


        if challenge is None:

            con.rollback()

            raise HTTPException(

                status_code=404,

                detail="Challenge not found",

            )


        status = str(

            challenge["status"]
            or ""

        ).upper()


        # ----------------------------------------------------
        # Prevent replay
        # ----------------------------------------------------

        if status != "PENDING":

            con.rollback()

            return {

                "status": "FAILED",

                "decision": "BLOCK",

                "risk_score":
                    challenge["risk_score"],

                "message": (

                    "This verification session "

                    "has already been completed."

                ),

            }


        # ----------------------------------------------------
        # Challenge expiry
        # ----------------------------------------------------

        try:

            expires = datetime.fromisoformat(

                challenge["expires_at"]

            )


            if utc_now() > expires:

                con.execute(

                    """

                    UPDATE challenge_sessions

                    SET status='EXPIRED'

                    WHERE challenge_id=?

                    """,

                    (payload.challenge_id,),

                )


                if challenge["transaction_id"]:

                    con.execute(

                        """

                        UPDATE transactions

                        SET

                            transaction_status='FAILED',

                            risk_decision='BLOCK'

                        WHERE transaction_id=?

                        """,

                        (
                            challenge[
                                "transaction_id"
                            ],
                        ),

                    )


                con.commit()


                return {

                    "status": "FAILED",

                    "decision": "BLOCK",

                    "risk_score":
                        challenge["risk_score"],

                    "message": (

                        "Verification expired. "

                        "Payment blocked."

                    ),

                }


        except ValueError:

            pass


        # ====================================================
        # CHECK ANSWER
        # ====================================================

        correct = answers_match(

            payload.answer,

            challenge["expected_answer"],

        )


        # ====================================================
        # WRONG ANSWER
        # ====================================================

        if not correct:

            con.execute(

                """

                UPDATE challenge_sessions

                SET status='FAILED'

                WHERE challenge_id=?

                """,

                (payload.challenge_id,),

            )


            if challenge["transaction_id"]:

                con.execute(

                    """

                    UPDATE transactions

                    SET

                        transaction_status='FAILED',

                        risk_decision='BLOCK'

                    WHERE transaction_id=?

                    """,

                    (
                        challenge[
                            "transaction_id"
                        ],
                    ),

                )


            con.commit()


            return {

                "status": "FAILED",

                "decision": "BLOCK",

                "risk_score":
                    challenge["risk_score"],

                "message": (

                    "Incorrect answer. "

                    "Payment blocked."

                ),

            }


        # ====================================================
        # CORRECT ANSWER
        #
        # THIS IS THE RELEASE PATH.
        #
        # The held transaction becomes SUCCESS and the balance
        # is deducted in the SAME database transaction.
        # ====================================================


        user = con.execute(

            """

            SELECT current_bank_balance

            FROM users

            WHERE user_id = ?

            """,

            (
                challenge[
                    "user_id"
                ],
            ),

        ).fetchone()


        if user is None:

            con.rollback()

            raise HTTPException(

                status_code=404,

                detail="Payer not found",

            )


        balance = float(

            user[
                "current_bank_balance"
            ]
            or 0

        )


        amount = float(

            challenge[
                "amount"
            ]

        )


        # ----------------------------------------------------
        # Recheck balance
        # ----------------------------------------------------

        if amount > balance:

            if challenge["transaction_id"]:

                con.execute(

                    """

                    UPDATE transactions

                    SET

                        transaction_status='FAILED',

                        risk_decision='BLOCK'

                    WHERE transaction_id=?

                    """,

                    (
                        challenge[
                            "transaction_id"
                        ],
                    ),

                )


            con.execute(

                """

                UPDATE challenge_sessions

                SET status='FAILED'

                WHERE challenge_id=?

                """,

                (payload.challenge_id,),

            )


            con.commit()


            return {

                "status":
                    "INSUFFICIENT_BALANCE",

                "decision":
                    "BLOCK",

                "risk_score":
                    challenge["risk_score"],

                "message": (

                    "Insufficient balance. "

                    "Payment could not be released."

                ),

            }


        new_balance = (
            balance - amount
        )


        # ----------------------------------------------------
        # Atomic deduction
        # ----------------------------------------------------

        updated = con.execute(

            """

            UPDATE users

            SET

                current_bank_balance = ?,

                total_transactions =

                    COALESCE(
                        total_transactions,
                        0
                    ) + 1

            WHERE

                user_id = ?

                AND current_bank_balance >= ?

            """,

            (

                new_balance,

                challenge["user_id"],

                amount,

            ),

        )


        if updated.rowcount != 1:

            con.rollback()

            return {

                "status":
                    "INSUFFICIENT_BALANCE",

                "decision":
                    "BLOCK",

                "risk_score":
                    challenge["risk_score"],

                "message": (

                    "Insufficient balance. "

                    "Payment could not be released."

                ),

            }


        # ----------------------------------------------------
        # RELEASE HELD TRANSACTION
        # ----------------------------------------------------

        if challenge["transaction_id"]:

            con.execute(

                """

                UPDATE transactions

                SET

                    transaction_status='SUCCESS',

                    risk_decision='ALLOW'

                WHERE transaction_id=?

                """,

                (
                    challenge[
                        "transaction_id"
                    ],
                ),

            )


        # ----------------------------------------------------
        # Mark challenge passed
        # ----------------------------------------------------

        con.execute(

            """

            UPDATE challenge_sessions

            SET status='PASSED'

            WHERE challenge_id=?

            """,

            (payload.challenge_id,),

        )


        # ----------------------------------------------------
        # Recalculate average
        # ----------------------------------------------------

        avg = con.execute(

            """

            SELECT AVG(amount)
                AS avg_amount

            FROM transactions

            WHERE user_id = ?

              AND UPPER(
                    COALESCE(
                        transaction_status,
                        ''
                    )
                  ) = 'SUCCESS'

            """,

            (
                challenge[
                    "user_id"
                ],
            ),

        ).fetchone()["avg_amount"]


        con.execute(

            """

            UPDATE users

            SET average_transaction = ?

            WHERE user_id = ?

            """,

            (

                float(avg or 0),

                challenge[
                    "user_id"
                ],

            ),

        )


        con.commit()


        # ====================================================
        # PAYMENT RELEASED
        # ====================================================

        return {

            "status": "SUCCESS",

            "decision": "ALLOW",

            "transaction_id":
                challenge["transaction_id"],

            "risk_score":
                challenge["risk_score"],

            "new_balance":
                new_balance,

            "message": (

                "Correct answer. "

                "Verification passed and the "

                "held payment has been released "

                "successfully."

            ),

        }


    except HTTPException:

        raise


    except Exception:

        con.rollback()

        raise


    finally:

        con.close()


# ============================================================
# RESET DASHBOARD
# ============================================================


@app.post("/reset-dashboard")
def reset_dashboard():

    con = get_connection()

    try:

        con.execute(
            "BEGIN IMMEDIATE"
        )


        # Remove demo challenge sessions.

        con.execute(
            "DELETE FROM challenge_sessions"
        )


        # Remove transaction history.

        con.execute(
            "DELETE FROM transactions"
        )


        # Restore exact starting balances.

        for user_id, balance in (
            INITIAL_BALANCES.items()
        ):

            con.execute(

                """

                UPDATE users

                SET

                    current_bank_balance = ?,

                    initial_bank_balance = ?,

                    average_transaction = 0,

                    total_transactions = 0

                WHERE user_id = ?

                """,

                (

                    balance,

                    balance,

                    user_id,

                ),

            )


        con.commit()


        return {

            "status": "ok",

            "message": (

                "SecureFlow-AI dashboard "

                "reset successfully."

            ),

        }


    except Exception:

        con.rollback()

        raise


    finally:

        con.close()


# Alias for compatibility
# with the frontend.

@app.post("/reset")
def reset_alias():

    return reset_dashboard()


# ============================================================
# START SERVER
# ============================================================


if __name__ == "__main__":

    import uvicorn


    print()
    print("=" * 65)
    print("        SECUREFLOW-AI BACKEND")
    print("=" * 65)
    print()
    print(f"Database : {DB_PATH}")
    print()
    print("API      : http://127.0.0.1:8000")
    print("Docs     : http://127.0.0.1:8000/docs")
    print()
    print("Risk:")
    print("  0 - 49   -> ALLOW")
    print("  50 - 79  -> HOLD + QUESTION")
    print("  80 - 100 -> BLOCK")
    print()
    print("Eight risk switches:")
    print("  Time anomaly")
    print("  Transaction frequency")
    print("  New device")
    print("  Unusual location")
    print("  Sudden location change")
    print("  Unknown beneficiary")
    print("  Previous transaction")
    print("  Typical amount")
    print()
    print("Amount deviation:")
    print("  <= ₹1000 -> 0 anomaly points")
    print("  >  ₹1000 -> historical pattern analysis")
    print()
    print("=" * 65)
    print()


    uvicorn.run(

        app,

        host="127.0.0.1",

        port=8000,

        reload=False,

    )
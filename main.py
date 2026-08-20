from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
from pathlib import Path
from datetime import datetime
import sqlite3
import uuid
import re

# ============================================================
# SecureFlow-AI FINAL BACKEND
#
# Flow:
# transaction
#      ↓
# risk engine
#      ↓
# risk < 50  → SUCCESS
# risk >= 50 → HOLD
#      ↓
# dynamic question from database
#      ↓
# correct → SUCCESS
# wrong   → FAILED
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "SecureFlow-AI4.db"

app = FastAPI(
    title="SecureFlow-AI Behaviour Engine",
    version="4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# FINAL RISK ENGINE
# Maximum = 100
# ============================================================

RISK_WEIGHTS = {
    "amount_deviation": 10,
    "time_anomaly": 7,
    "frequency_anomaly": 12,
    "new_device": 15,
    "unusual_location": 15,
    "sudden_location_change": 6,
    "unknown_beneficiary": 12,
    "no_previous_transaction": 13,
    "unusual_beneficiary_amount": 10,
}

HOLD_THRESHOLD = 50


# ============================================================
# DATABASE
# ============================================================

def db():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                f"{DB_PATH.name} was not found. "
                "Put the database file in the same folder as main.py."
            ),
        )

    con = sqlite3.connect(
        str(DB_PATH),
        timeout=15
    )

    con.row_factory = sqlite3.Row

    con.execute("PRAGMA foreign_keys = ON")

    return con


# ============================================================
# VERIFICATION TABLE
# ============================================================

def initialize_challenge_table():

    con = db()

    try:

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS verification_challenges (

                challenge_id TEXT PRIMARY KEY,

                transaction_id TEXT NOT NULL UNIQUE,

                question TEXT NOT NULL,

                answer_type TEXT NOT NULL,

                expected_answer TEXT NOT NULL,

                tolerance REAL DEFAULT 0,

                source TEXT,

                created_at TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'PENDING',

                FOREIGN KEY(transaction_id)
                    REFERENCES transactions(transaction_id)
                    ON DELETE CASCADE,

                CHECK(
                    status IN ('PENDING', 'PASSED', 'FAILED')
                )
            )
            """
        )

        con.commit()

    finally:

        con.close()


@app.on_event("startup")
def startup():

    initialize_challenge_table()


# ============================================================
# REQUEST MODELS
# ============================================================

class TransactionRequest(BaseModel):

    # Payer MUST exist in database
    user_id: str

    # Recipient MUST exist in database
    recipient_upi_id: str

    amount: float = Field(gt=0)

    # ONLY FINAL RISK ENGINE CONTROLS

    amount_deviation: bool = False

    time_anomaly: bool = False

    frequency_anomaly: bool = False

    new_device: bool = False

    unusual_location: bool = False

    sudden_location_change: bool = False

    unknown_beneficiary: bool = False

    no_previous_transaction: bool = False

    unusual_beneficiary_amount: bool = False

    # Optional context

    device_name: Optional[str] = None

    payment_location: Optional[str] = None


class VerifyRequest(BaseModel):

    transaction_id: str

    answer: str


# ============================================================
# HELPERS
# ============================================================

def norm(value):

    return re.sub(
        r"\s+",
        " ",
        str(value or "").strip()
    ).lower()


def row_dict(row):

    if row:

        return dict(row)

    return None


# ============================================================
# GET PAYER
# ============================================================

def get_user(con, user_id):

    row = con.execute(
        """
        SELECT
            user_id,
            name,
            date_of_birth,
            college_name,
            living_area,
            known_device,
            common_location,
            average_transaction,
            total_transactions
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    if not row:

        raise HTTPException(
            status_code=404,
            detail="Payer was not found in the database."
        )

    return row


# ============================================================
# GET RECIPIENT
# ============================================================

def get_recipient(con, upi_id):

    row = con.execute(
        """
        SELECT
            recipient_id,
            recipient_name,
            upi_id,
            recipient_device_name,
            recipient_location,
            recipient_type
        FROM recipients
        WHERE lower(upi_id) = lower(?)
        """,
        (upi_id,)
    ).fetchone()

    if not row:

        raise HTTPException(
            status_code=404,
            detail="Recipient UPI ID was not found in the database."
        )

    return row


# ============================================================
# PAYER → RECIPIENT CONNECTION
# ============================================================

def get_connection(
    con,
    user_id,
    recipient_id
):

    return con.execute(
        """
        SELECT
            connection_id,
            user_id,
            recipient_id,
            previous_connection,
            connection_type,
            previous_transaction_count,
            connection_notes
        FROM sender_recipient_connections
        WHERE user_id = ?
        AND recipient_id = ?
        """,
        (
            user_id,
            recipient_id
        )
    ).fetchone()


# ============================================================
# RECIPIENT TRANSACTION AVERAGE
# ============================================================

def get_recipient_average(
    con,
    user_id,
    recipient_id
):

    row = con.execute(
        """
        SELECT
            AVG(amount) AS avg_amount,
            COUNT(*) AS count
        FROM transactions
        WHERE user_id = ?
        AND recipient_id = ?
        AND transaction_status = 'SUCCESS'
        """,
        (
            user_id,
            recipient_id
        )
    ).fetchone()

    if not row:

        return None, 0

    if row["avg_amount"] is None:

        return None, 0

    return (
        float(row["avg_amount"]),
        int(row["count"] or 0)
    )


# ============================================================
# COMMON PAYMENT TIME
# ============================================================

def get_common_payment_hour(
    con,
    user_id
):

    rows = con.execute(
        """
        SELECT transaction_time
        FROM transactions
        WHERE user_id = ?
        AND transaction_status = 'SUCCESS'
        """,
        (user_id,)
    ).fetchall()

    counts = {}

    for row in rows:

        raw = str(
            row["transaction_time"]
        )

        try:

            hour = datetime.fromisoformat(
                raw
            ).hour

        except Exception:

            try:

                hour = datetime.strptime(
                    raw[:16],
                    "%Y-%m-%d %H:%M"
                ).hour

            except Exception:

                continue

        counts[hour] = (
            counts.get(hour, 0) + 1
        )

    if not counts:

        return None

    return max(
        counts,
        key=counts.get
    )


# ============================================================
# DYNAMIC QUESTION ENGINE
#
# No Rahul/Amit/etc. are hard-coded.
#
# Questions and expected answers come from the DB.
# ============================================================

def build_dynamic_question(
    con,
    user,
    recipient,
    connection,
    triggered_signals,
    amount
):

    user_id = user["user_id"]

    recipient_id = recipient["recipient_id"]

    recipient_avg, recipient_count = (
        get_recipient_average(
            con,
            user_id,
            recipient_id
        )
    )

    # --------------------------------------------------------
    # NEW DEVICE
    # --------------------------------------------------------

    if "new_device" in triggered_signals:

        return {

            "question":
                "Security verification: what device do you "
                "normally use for payments?",

            "answer_type":
                "text",

            "expected_answer":
                user["known_device"],

            "tolerance":
                0,

            "source":
                "users.known_device"
        }

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    if (
        "unusual_location" in triggered_signals
        or
        "sudden_location_change" in triggered_signals
    ):

        return {

            "question":
                "Security verification: what is your usual "
                "payment location?",

            "answer_type":
                "text",

            "expected_answer":
                user["common_location"],

            "tolerance":
                0,

            "source":
                "users.common_location"
        }

    # --------------------------------------------------------
    # UNKNOWN BENEFICIARY
    # --------------------------------------------------------

    if "unknown_beneficiary" in triggered_signals:

        return {

            "question":
                f"Security verification: what type of recipient "
                f"is {recipient['recipient_name']}?",

            "answer_type":
                "text",

            "expected_answer":
                recipient["recipient_type"],

            "tolerance":
                0,

            "source":
                "recipients.recipient_type"
        }

    # --------------------------------------------------------
    # NO PREVIOUS TRANSACTION
    # --------------------------------------------------------

    if "no_previous_transaction" in triggered_signals:

        previous_count = (

            int(
                connection[
                    "previous_transaction_count"
                ]
            )

            if connection

            else 0
        )

        return {

            "question":
                f"Security verification: how many previous "
                f"payments are recorded with "
                f"{recipient['recipient_name']}?",

            "answer_type":
                "number",

            "expected_answer":
                str(previous_count),

            "tolerance":
                0,

            "source":
                "sender_recipient_connections."
                "previous_transaction_count"
        }

    # --------------------------------------------------------
    # UNUSUAL BENEFICIARY AMOUNT
    # --------------------------------------------------------

    if "unusual_beneficiary_amount" in triggered_signals:

        if recipient_avg is not None:

            tolerance = max(
                100.0,
                recipient_avg * 0.20
            )

            return {

                "question":
                    f"Security verification: approximately how "
                    f"much do you usually send to "
                    f"{recipient['recipient_name']}?",

                "answer_type":
                    "amount",

                "expected_answer":
                    str(recipient_avg),

                "tolerance":
                    tolerance,

                "source":
                    "transactions.amount"
            }

        stored_average = float(
            user["average_transaction"] or 0
        )

        return {

            "question":
                "Security verification: approximately what is "
                "your usual payment amount?",

            "answer_type":
                "amount",

            "expected_answer":
                str(stored_average),

            "tolerance":
                max(
                    100.0,
                    stored_average * 0.20
                ),

            "source":
                "users.average_transaction"
        }

    # --------------------------------------------------------
    # AMOUNT DEVIATION
    # --------------------------------------------------------

    if "amount_deviation" in triggered_signals:

        stored_average = float(
            user["average_transaction"] or 0
        )

        return {

            "question":
                "Security verification: approximately what is "
                "your usual payment amount?",

            "answer_type":
                "amount",

            "expected_answer":
                str(stored_average),

            "tolerance":
                max(
                    100.0,
                    stored_average * 0.20
                ),

            "source":
                "users.average_transaction"
        }

    # --------------------------------------------------------
    # TIME ANOMALY
    # --------------------------------------------------------

    if "time_anomaly" in triggered_signals:

        common_hour = get_common_payment_hour(
            con,
            user_id
        )

        if common_hour is not None:

            display_hour = datetime(
                2000,
                1,
                1,
                common_hour
            ).strftime(
                "%I %p"
            ).lstrip("0")

            return {

                "question":
                    "Security verification: around what time "
                    "do you usually make payments?",

                "answer_type":
                    "time",

                "expected_answer":
                    str(common_hour),

                "expected_display":
                    display_hour,

                "tolerance":
                    0,

                "source":
                    "transactions.transaction_time"
            }

    # --------------------------------------------------------
    # FREQUENCY
    # --------------------------------------------------------

    if "frequency_anomaly" in triggered_signals:

        return {

            "question":
                "Security verification: how many successful "
                "transactions are recorded in your account "
                "history?",

            "answer_type":
                "number",

            "expected_answer":
                str(
                    int(
                        user["total_transactions"] or 0
                    )
                ),

            "tolerance":
                0,

            "source":
                "users.total_transactions"
        }

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    return {

        "question":
            "Security verification: what is your registered "
            "payment location?",

        "answer_type":
            "text",

        "expected_answer":
            user["common_location"],

        "tolerance":
            0,

        "source":
            "users.common_location"
    }


# ============================================================
# VERIFY ANSWER
# ============================================================

def check_answer(
    challenge,
    supplied_answer
):

    supplied = norm(
        supplied_answer
    )

    if not supplied:

        return False

    expected = challenge[
        "expected_answer"
    ]

    answer_type = challenge[
        "answer_type"
    ]

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    if answer_type == "text":

        return (
            supplied
            ==
            norm(expected)
        )

    # --------------------------------------------------------
    # NUMBER
    # --------------------------------------------------------

    if answer_type == "number":

        try:

            return (
                int(float(supplied))
                ==
                int(float(expected))
            )

        except Exception:

            return False

    # --------------------------------------------------------
    # AMOUNT
    # --------------------------------------------------------

    if answer_type == "amount":

        try:

            value = float(
                supplied
                .replace("₹", "")
                .replace(",", "")
            )

            target = float(
                expected
            )

            tolerance = float(
                challenge["tolerance"] or 0
            )

            return (
                abs(value - target)
                <= tolerance
            )

        except Exception:

            return False

    # --------------------------------------------------------
    # TIME
    # --------------------------------------------------------

    if answer_type == "time":

        try:

            if supplied.isdigit():

                return (
                    int(supplied)
                    ==
                    int(float(expected))
                )

        except Exception:

            pass

        match = re.search(
            r"\b(\d{1,2})(?::\d{2})?\s*(am|pm)?\b",
            supplied,
            re.IGNORECASE
        )

        if not match:

            return False

        hour = int(
            match.group(1)
        )

        ampm = (
            match.group(2)
            or ""
        ).lower()

        if (
            ampm == "pm"
            and
            hour != 12
        ):

            hour += 12

        elif (
            ampm == "am"
            and
            hour == 12
        ):

            hour = 0

        return (
            hour
            ==
            int(float(expected))
        )

    return False


# ============================================================
# RISK ENGINE
# ============================================================

def calculate_risk(tx):

    signals = {

        "amount_deviation":
            tx.amount_deviation,

        "time_anomaly":
            tx.time_anomaly,

        "frequency_anomaly":
            tx.frequency_anomaly,

        "new_device":
            tx.new_device,

        "unusual_location":
            tx.unusual_location,

        "sudden_location_change":
            tx.sudden_location_change,

        "unknown_beneficiary":
            tx.unknown_beneficiary,

        "no_previous_transaction":
            tx.no_previous_transaction,

        "unusual_beneficiary_amount":
            tx.unusual_beneficiary_amount,
    }

    labels = {

        "amount_deviation":
            "Amount deviation",

        "time_anomaly":
            "Time anomaly",

        "frequency_anomaly":
            "Transaction frequency anomaly",

        "new_device":
            "New device/session",

        "unusual_location":
            "Location anomaly",

        "sudden_location_change":
            "Sudden location change",

        "unknown_beneficiary":
            "Unknown beneficiary",

        "no_previous_transaction":
            "No previous transaction",

        "unusual_beneficiary_amount":
            "Unusual amount for this beneficiary",
    }

    score = 0

    triggered = []

    reasons = []

    for key, active in signals.items():

        if active:

            score += RISK_WEIGHTS[key]

            triggered.append(
                key
            )

            reasons.append(
                labels[key]
            )

    # NEVER allow >100

    score = max(
        0,
        min(
            100,
            score
        )
    )

    return (
        score,
        triggered,
        reasons
    )


# ============================================================
# HOME
# ============================================================

@app.get("/")
def root():

    return {

        "message":
            "SecureFlow-AI Behaviour Engine",

        "status":
            "online",

        "database":
            DB_PATH.name,

        "hold_threshold":
            HOLD_THRESHOLD,

        "risk_max":
            100
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    con = db()

    try:

        return {

            "status":
                "healthy",

            "database":
                DB_PATH.name,

            "users":
                con.execute(
                    "SELECT COUNT(*) FROM users"
                ).fetchone()[0],

            "recipients":
                con.execute(
                    "SELECT COUNT(*) FROM recipients"
                ).fetchone()[0],

            "transactions":
                con.execute(
                    "SELECT COUNT(*) FROM transactions"
                ).fetchone()[0],
        }

    finally:

        con.close()


# ============================================================
# USERS
# ============================================================

@app.get("/users")
def list_users():

    con = db()

    try:

        rows = con.execute(
            """
            SELECT
                user_id,
                name,
                living_area,
                known_device,
                common_location,
                average_transaction,
                total_transactions
            FROM users
            ORDER BY user_id
            """
        ).fetchall()

        return {

            "users":
                [
                    row_dict(row)
                    for row in rows
                ]
        }

    finally:

        con.close()


# ============================================================
# RECIPIENTS
# ============================================================

@app.get("/recipients")
def list_recipients():

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

            "recipients":
                [
                    row_dict(row)
                    for row in rows
                ]
        }

    finally:

        con.close()


# ============================================================
# RECIPIENTS FOR A PARTICULAR PAYER
# ============================================================

@app.get("/users/{user_id}/recipients")
def list_user_recipients(
    user_id: str
):

    con = db()

    try:

        user = get_user(
            con,
            user_id
        )

        rows = con.execute(
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

                ON c.recipient_id =
                   r.recipient_id

                AND c.user_id = ?

            ORDER BY r.recipient_name
            """,
            (user_id,)
        ).fetchall()

        return {

            "payer": {

                "user_id":
                    user["user_id"],

                "name":
                    user["name"],
            },

            "recipients":
                [
                    row_dict(row)
                    for row in rows
                ]
        }

    finally:

        con.close()


# ============================================================
# CREATE / ANALYZE TRANSACTION
# ============================================================

@app.post("/transaction")
def create_transaction(
    tx: TransactionRequest
):

    con = db()

    try:

        # ----------------------------------------------------
        # DATABASE LOOKUP
        # ----------------------------------------------------

        user = get_user(
            con,
            tx.user_id
        )

        recipient = get_recipient(
            con,
            tx.recipient_upi_id
        )

        connection = get_connection(
            con,
            user["user_id"],
            recipient["recipient_id"]
        )

        # ----------------------------------------------------
        # RISK ENGINE
        # ----------------------------------------------------

        score, triggered, reasons = (
            calculate_risk(tx)
        )

        transaction_id = (
            "SF-"
            +
            uuid.uuid4()
            .hex[:12]
            .upper()
        )

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        sender_device = (

            tx.device_name

            if tx.device_name

            else user["known_device"]
        )

        payment_location = (

            tx.payment_location

            if tx.payment_location

            else user["common_location"]
        )

        previous_connection = (

            int(
                connection[
                    "previous_connection"
                ]
            )

            if connection

            else 0
        )

        # ----------------------------------------------------
        # SCORE >= 50 = HOLD
        # SCORE < 50 = SUCCESS
        # ----------------------------------------------------

        held = (
            score
            >=
            HOLD_THRESHOLD
        )

        status = (
            "HELD"
            if held
            else
            "SUCCESS"
        )

        # ----------------------------------------------------
        # SAVE TRANSACTION
        # ----------------------------------------------------

        con.execute(
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
                transaction_status
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                transaction_id,

                user["user_id"],

                recipient["recipient_id"],

                tx.amount,

                now,

                sender_device,

                recipient[
                    "recipient_device_name"
                ],

                payment_location,

                user[
                    "common_location"
                ],

                previous_connection,

                status,
            )
        )

        response = {

            "transaction_id":
                transaction_id,

            "payer": {

                "user_id":
                    user["user_id"],

                "name":
                    user["name"],
            },

            "recipient": {

                "recipient_id":
                    recipient[
                        "recipient_id"
                    ],

                "name":
                    recipient[
                        "recipient_name"
                    ],

                "upi_id":
                    recipient[
                        "upi_id"
                    ],
            },

            "amount":
                tx.amount,

            "risk_score":
                score,

            "risk_max":
                100,

            "decision":
                "HOLD"
                if held
                else
                "ALLOW",

            "status":
                status,

            "reasons":
                reasons,

            "verification_required":
                held,
        }

        # ----------------------------------------------------
        # DYNAMIC QUESTION
        # ONLY IF RISK >= 50
        # ----------------------------------------------------

        if held:

            challenge = (
                build_dynamic_question(

                    con=con,

                    user=user,

                    recipient=recipient,

                    connection=connection,

                    triggered_signals=triggered,

                    amount=tx.amount
                )
            )

            challenge_id = (
                "CH-"
                +
                uuid.uuid4()
                .hex[:12]
                .upper()
            )

            con.execute(
                """
                INSERT INTO
                verification_challenges
                (
                    challenge_id,
                    transaction_id,
                    question,
                    answer_type,
                    expected_answer,
                    tolerance,
                    source,
                    created_at,
                    status
                )
                VALUES
                (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, 'PENDING'
                )
                """,
                (
                    challenge_id,

                    transaction_id,

                    challenge["question"],

                    challenge[
                        "answer_type"
                    ],

                    str(
                        challenge[
                            "expected_answer"
                        ]
                    ),

                    float(
                        challenge.get(
                            "tolerance",
                            0
                        )
                    ),

                    challenge[
                        "source"
                    ],

                    now,
                )
            )

            response["message"] = (
                "Payment held. "
                "Behavioural verification required."
            )

            # IMPORTANT:
            # expected_answer is NEVER sent.

            response[
                "verification"
            ] = {

                "challenge_id":
                    challenge_id,

                "question":
                    challenge[
                        "question"
                    ],

                "answer_type":
                    challenge[
                        "answer_type"
                    ],
            }

        else:

            response["message"] = (
                "Payment completed successfully."
            )

        con.commit()

        return response

    except HTTPException:

        con.rollback()

        raise

    except sqlite3.IntegrityError as exc:

        con.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Database integrity error: {exc}"
            )
        )

    except Exception as exc:

        con.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Transaction processing failed: "
                f"{exc}"
            )
        )

    finally:

        con.close()


# ============================================================
# VERIFY PAYMENT
# ============================================================

@app.post("/verify")
def verify_transaction(
    request: VerifyRequest
):

    con = db()

    try:

        # ----------------------------------------------------
        # FIND PENDING QUESTION
        # ----------------------------------------------------

        challenge = con.execute(
            """
            SELECT
                challenge_id,
                transaction_id,
                question,
                answer_type,
                expected_answer,
                tolerance,
                status
            FROM verification_challenges
            WHERE transaction_id = ?
            AND status = 'PENDING'
            """,
            (
                request.transaction_id,
            )
        ).fetchone()

        if not challenge:

            raise HTTPException(
                status_code=404,
                detail=(
                    "No pending verification "
                    "exists for this transaction."
                )
            )

        # ----------------------------------------------------
        # FIND TRANSACTION
        # ----------------------------------------------------

        transaction = con.execute(
            """
            SELECT
                transaction_id,
                transaction_status
            FROM transactions
            WHERE transaction_id = ?
            """,
            (
                request.transaction_id,
            )
        ).fetchone()

        if not transaction:

            raise HTTPException(
                status_code=404,
                detail="Transaction not found."
            )

        if (
            transaction[
                "transaction_status"
            ]
            !=
            "HELD"
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "This transaction is not "
                    "waiting for verification."
                )
            )

        # ----------------------------------------------------
        # CHECK ANSWER
        # ----------------------------------------------------

        correct = check_answer(
            challenge,
            request.answer
        )

        # ----------------------------------------------------
        # CORRECT
        # ----------------------------------------------------

        if correct:

            new_status = "SUCCESS"

            decision = "COMPLETE"

            message = (
                "Verification successful. "
                "Payment completed."
            )

            challenge_status = "PASSED"

        # ----------------------------------------------------
        # WRONG
        # ----------------------------------------------------

        else:

            new_status = "FAILED"

            decision = "CANCEL"

            message = (
                "Verification failed. "
                "Payment cancelled."
            )

            challenge_status = "FAILED"

        # ----------------------------------------------------
        # UPDATE PAYMENT
        # ----------------------------------------------------

        con.execute(
            """
            UPDATE transactions
            SET transaction_status = ?
            WHERE transaction_id = ?
            """,
            (
                new_status,
                request.transaction_id
            )
        )

        # ----------------------------------------------------
        # UPDATE VERIFICATION
        # ----------------------------------------------------

        con.execute(
            """
            UPDATE verification_challenges
            SET status = ?
            WHERE transaction_id = ?
            """,
            (
                challenge_status,
                request.transaction_id
            )
        )

        con.commit()

        return {

            "transaction_id":
                request.transaction_id,

            "verified":
                correct,

            "decision":
                decision,

            "status":
                new_status,

            "message":
                message
        }

    except HTTPException:

        con.rollback()

        raise

    except Exception as exc:

        con.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Verification processing failed: "
                f"{exc}"
            )
        )

    finally:

        con.close()


# ============================================================
# TRANSACTION STATUS
# ============================================================

@app.get(
    "/transaction/{transaction_id}"
)
def get_transaction(
    transaction_id: str
):

    con = db()

    try:

        row = con.execute(
            """
            SELECT

                t.transaction_id,

                t.amount,

                t.transaction_time,

                t.payment_location,

                t.transaction_status,

                u.user_id,

                u.name AS payer_name,

                r.recipient_id,

                r.recipient_name,

                r.upi_id AS recipient_upi_id

            FROM transactions t

            JOIN users u
                ON u.user_id = t.user_id

            JOIN recipients r
                ON r.recipient_id = t.recipient_id

            WHERE t.transaction_id = ?
            """,
            (
                transaction_id,
            )
        ).fetchone()

        if not row:

            raise HTTPException(
                status_code=404,
                detail="Transaction not found."
            )

        return row_dict(row)

    finally:

        con.close()


# ============================================================
# START SERVER FROM TERMINAL:
#
# python -m uvicorn main:app --reload
#
# DO NOT PUT THAT COMMAND INSIDE THIS FILE.
# ============================================================
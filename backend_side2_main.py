from __future__ import annotations

import hashlib
import json
import random
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from sklearn.ensemble import RandomForestRegressor
except Exception:
    RandomForestRegressor = None


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

# Put this backend.py in the same folder as SecureFlow-AI8.db.
# If the database does not contain the required tables, they
# will automatically be created.
DB_PATH = BASE_DIR / "SecureFlow-AI8.db"

app = FastAPI(
    title="SecureFlow AI Risk Engine",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# RISK ENGINE
# ============================================================
#
# Your paper contains 9 factors:
#
# 1. Amount
# 2. Time
# 3. Frequency
# 4. New Device
# 5. Unusual Location
# 6. Sudden Location Change
# 7. Unknown Beneficiary
# 8. Previous Transaction
# 9. Typical Amount
#
# Amount is NOT displayed as a checkbox.
# It is calculated internally only when amount > 1000.
#
# Therefore exactly 8 switches are exposed.
# ============================================================

RISK_WEIGHTS = {
    "time_anomaly": 7,
    "transaction_frequency": 12,
    "new_device": 15,
    "unusual_location": 15,
    "sudden_location_change": 6,
    "unknown_beneficiary": 12,
    "previous_transaction": 13,
    "typical_amount": 10,
}

AMOUNT_WEIGHT = 10


# ============================================================
# DYNAMIC QUESTION PRIORITY
# ============================================================

QUESTION_PRIORITY = {
    "new_device": [
        "DEVICE_CONFIRM",
    ],

    "unusual_location": [
        "AREA_CONFIRM",
        "LOCATION_CONFIRM",
    ],

    "sudden_location_change": [
        "LOCATION_CONFIRM",
        "AREA_CONFIRM",
    ],

    "unknown_beneficiary": [
        "RECIPIENT_CONFIRM",
        "NEARBY_PLACE_CONFIRM",
    ],

    "previous_transaction": [
        "HISTORY_CONFIRM",
    ],

    "time_anomaly": [
        "COLLEGE_CONFIRM",
        "DOB_CONFIRM",
    ],

    "transaction_frequency": [
        "HISTORY_CONFIRM",
        "RECIPIENT_CONFIRM",
    ],

    "typical_amount": [
        "HISTORY_CONFIRM",
        "RECIPIENT_CONFIRM",
    ],
}


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize(value: Any) -> str:
    return " ".join(
        str(value or "")
        .strip()
        .casefold()
        .split()
    )


def answer_matches(
    expected: str,
    actual: str,
    answer_type: str,
) -> bool:

    expected_normalized = normalize(expected)
    actual_normalized = normalize(actual)

    if answer_type == "YES_NO":

        if (
            actual_normalized in {"yes", "y"}
            and expected_normalized in {"yes", "y"}
        ):
            return True

        if (
            actual_normalized in {"no", "n"}
            and expected_normalized in {"no", "n"}
        ):
            return True

        return False

    return expected_normalized == actual_normalized


def get_conn() -> sqlite3.Connection:

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.execute(
        "PRAGMA journal_mode = WAL"
    )

    return conn


def row_to_dict(
    row: sqlite3.Row,
) -> Dict[str, Any]:

    return dict(row)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db() -> None:

    conn = get_conn()

    try:

        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS payees (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                upi_id TEXT NOT NULL UNIQUE
            );


            CREATE TABLE IF NOT EXISTS dynamic_question_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id TEXT NOT NULL,

                name TEXT NOT NULL,

                question_id INTEGER NOT NULL,

                question_code TEXT NOT NULL,

                question_text TEXT NOT NULL,

                risk_factor TEXT NOT NULL,

                expected_answer_type TEXT NOT NULL,

                expected_answer TEXT NOT NULL,

                UNIQUE(user_id, question_code)
            );


            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id TEXT PRIMARY KEY,

                payer_id TEXT NOT NULL,

                recipient_name TEXT NOT NULL,

                recipient_upi_id TEXT NOT NULL,

                amount REAL NOT NULL,

                risk_score INTEGER,

                decision TEXT NOT NULL,

                status TEXT NOT NULL,

                signals_json TEXT,

                amount_deviation REAL NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS challenges (
                challenge_id TEXT PRIMARY KEY,

                transaction_id TEXT NOT NULL UNIQUE,

                payer_id TEXT NOT NULL,

                question_id INTEGER NOT NULL,

                question_code TEXT NOT NULL,

                question_text TEXT NOT NULL,

                expected_answer_type TEXT NOT NULL,

                expected_answer TEXT NOT NULL,

                expires_at TEXT NOT NULL,

                used INTEGER NOT NULL DEFAULT 0
            );


            CREATE TABLE IF NOT EXISTS devices (
                payer_id TEXT NOT NULL,

                device_hash TEXT NOT NULL,

                first_seen TEXT NOT NULL,

                last_seen TEXT NOT NULL,

                PRIMARY KEY (
                    payer_id,
                    device_hash
                )
            );


            CREATE TABLE IF NOT EXISTS locations (
                payer_id TEXT PRIMARY KEY,

                last_location TEXT,

                last_seen TEXT NOT NULL
            );
            """
        )


        # ====================================================
        # FOUR PAYERS
        # ====================================================

        payees = [

            (
                "U001",
                "Soumadip Das",
                55000.0,
                "soumadip@upi",
            ),

            (
                "U002",
                "Shubham Paul",
                60000.0,
                "shubham.paul@upi",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                50000.0,
                "shubham.mukherjee@upi",
            ),

            (
                "U004",
                "Tridip Debroy",
                40000.0,
                "tridip.debroy@upi",
            ),
        ]


        for row in payees:

            conn.execute(
                """
                INSERT OR IGNORE INTO payees
                (
                    user_id,
                    name,
                    balance,
                    upi_id
                )
                VALUES (?, ?, ?, ?)
                """,
                row,
            )


        # ====================================================
        # DYNAMIC QUESTIONS
        # ====================================================
        #
        # These are based on the supplied screenshots.
        #
        # AMOUNT_CONFIRM IS INTENTIONALLY NOT INSERTED.
        #
        # That keeps the amount out of the dynamic
        # authentication question system.
        # ====================================================

        questions = [

            # ------------------------------------------------
            # DEVICE
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                5,
                "DEVICE_CONFIRM",
                "Which device do you normally use for payments?",
                "Known device",
                "TEXT",
                "Samsung Galaxy S23 - SOUMADIP",
            ),

            (
                "U002",
                "Shubham Paul",
                5,
                "DEVICE_CONFIRM",
                "Which device do you normally use for payments?",
                "Known device",
                "TEXT",
                "OnePlus 12R - SHUBHAM",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                5,
                "DEVICE_CONFIRM",
                "Which device do you normally use for payments?",
                "Known device",
                "TEXT",
                "Redmi Note 13 Pro - MUKHERJEE",
            ),

            (
                "U004",
                "Tridip Debroy",
                5,
                "DEVICE_CONFIRM",
                "Which device do you normally use for payments?",
                "Known device",
                "TEXT",
                "Google Pixel 8 - TRIDIP",
            ),


            # ------------------------------------------------
            # AREA
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                3,
                "AREA_CONFIRM",
                "Which area do you live in?",
                "Residential identity",
                "TEXT",
                "Haldia",
            ),

            (
                "U002",
                "Shubham Paul",
                3,
                "AREA_CONFIRM",
                "Which area do you live in?",
                "Residential identity",
                "TEXT",
                "Haldia",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                3,
                "AREA_CONFIRM",
                "Which area do you live in?",
                "Residential identity",
                "TEXT",
                "Haldia",
            ),

            (
                "U004",
                "Tridip Debroy",
                3,
                "AREA_CONFIRM",
                "Which area do you live in?",
                "Residential identity",
                "TEXT",
                "Haldia",
            ),


            # ------------------------------------------------
            # LOCATION
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                6,
                "LOCATION_CONFIRM",
                "What is your usual payment location?",
                "Location familiarity",
                "TEXT",
                "Haldia",
            ),

            (
                "U002",
                "Shubham Paul",
                6,
                "LOCATION_CONFIRM",
                "What is your usual payment location?",
                "Location familiarity",
                "TEXT",
                "Kolkata",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                6,
                "LOCATION_CONFIRM",
                "What is your usual payment location?",
                "Location familiarity",
                "TEXT",
                "Haldia",
            ),

            (
                "U004",
                "Tridip Debroy",
                6,
                "LOCATION_CONFIRM",
                "What is your usual payment location?",
                "Location familiarity",
                "TEXT",
                "Kolkata",
            ),


            # ------------------------------------------------
            # DOB
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                1,
                "DOB_CONFIRM",
                "What is your date of birth?",
                "Personal identity",
                "TEXT",
                "2005-04-18",
            ),

            (
                "U002",
                "Shubham Paul",
                1,
                "DOB_CONFIRM",
                "What is your date of birth?",
                "Personal identity",
                "TEXT",
                "2004-11-07",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                1,
                "DOB_CONFIRM",
                "What is your date of birth?",
                "Personal identity",
                "TEXT",
                "2005-02-21",
            ),

            (
                "U004",
                "Tridip Debroy",
                1,
                "DOB_CONFIRM",
                "What is your date of birth?",
                "Personal identity",
                "TEXT",
                "2004-08-13",
            ),


            # ------------------------------------------------
            # COLLEGE
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                2,
                "COLLEGE_CONFIRM",
                "What is the name of your college?",
                "Personal identity",
                "TEXT",
                "Haldia Institute of Technology",
            ),

            (
                "U002",
                "Shubham Paul",
                2,
                "COLLEGE_CONFIRM",
                "What is the name of your college?",
                "Personal identity",
                "TEXT",
                "Haldia Institute of Technology",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                2,
                "COLLEGE_CONFIRM",
                "What is the name of your college?",
                "Personal identity",
                "TEXT",
                "Haldia Institute of Technology",
            ),

            (
                "U004",
                "Tridip Debroy",
                2,
                "COLLEGE_CONFIRM",
                "What is the name of your college?",
                "Personal identity",
                "TEXT",
                "Haldia Institute of Technology",
            ),


            # ------------------------------------------------
            # NEARBY PLACE
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                4,
                "NEARBY_PLACE_CONFIRM",
                "Tell us one well-known place near your home.",
                "Residential knowledge",
                "TEXT",
                "Haldia Railway Station",
            ),

            (
                "U002",
                "Shubham Paul",
                4,
                "NEARBY_PLACE_CONFIRM",
                "Tell us one well-known place near your home.",
                "Residential knowledge",
                "TEXT",
                "Haldia Township",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                4,
                "NEARBY_PLACE_CONFIRM",
                "Tell us one well-known place near your home.",
                "Residential knowledge",
                "TEXT",
                "Haldia Dock Complex",
            ),

            (
                "U004",
                "Tridip Debroy",
                4,
                "NEARBY_PLACE_CONFIRM",
                "Tell us one well-known place near your home.",
                "Residential knowledge",
                "TEXT",
                "Haldia Township",
            ),


            # ------------------------------------------------
            # HISTORY
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                8,
                "HISTORY_CONFIRM",
                "Have you previously made a payment to this recipient?",
                "Transaction history",
                "YES_NO",
                "YES",
            ),

            (
                "U002",
                "Shubham Paul",
                8,
                "HISTORY_CONFIRM",
                "Have you previously made a payment to this recipient?",
                "Transaction history",
                "YES_NO",
                "YES",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                8,
                "HISTORY_CONFIRM",
                "Have you previously made a payment to this recipient?",
                "Transaction history",
                "YES_NO",
                "YES",
            ),

            (
                "U004",
                "Tridip Debroy",
                8,
                "HISTORY_CONFIRM",
                "Have you previously made a payment to this recipient?",
                "Transaction history",
                "YES_NO",
                "YES",
            ),


            # ------------------------------------------------
            # RECIPIENT
            # ------------------------------------------------

            (
                "U001",
                "Soumadip Das",
                7,
                "RECIPIENT_CONFIRM",
                "Do you recognize the recipient of this payment?",
                "Recipient familiarity",
                "YES_NO",
                "YES",
            ),

            (
                "U002",
                "Shubham Paul",
                7,
                "RECIPIENT_CONFIRM",
                "Do you recognize the recipient of this payment?",
                "Recipient familiarity",
                "YES_NO",
                "YES",
            ),

            (
                "U003",
                "Shubham Mukherjee",
                7,
                "RECIPIENT_CONFIRM",
                "Do you recognize the recipient of this payment?",
                "Recipient familiarity",
                "YES_NO",
                "YES",
            ),

            (
                "U004",
                "Tridip Debroy",
                7,
                "RECIPIENT_CONFIRM",
                "Do you recognize the recipient of this payment?",
                "Recipient familiarity",
                "YES_NO",
                "YES",
            ),
        ]


        conn.executemany(
            """
            INSERT OR IGNORE INTO dynamic_question_data
            (
                user_id,
                name,
                question_id,
                question_code,
                question_text,
                risk_factor,
                expected_answer_type,
                expected_answer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            questions,
        )


        conn.commit()

    finally:

        conn.close()


init_db()


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_payer(
    conn: sqlite3.Connection,
    payer_id: str,
) -> sqlite3.Row:

    row = conn.execute(
        """
        SELECT *
        FROM payees
        WHERE user_id=?
        """,
        (payer_id,),
    ).fetchone()


    if not row:

        raise HTTPException(
            status_code=404,
            detail="Payer not found.",
        )


    return row


def get_history(
    conn: sqlite3.Connection,
    payer_id: str,
) -> List[sqlite3.Row]:

    return conn.execute(
        """
        SELECT *
        FROM transactions
        WHERE payer_id=?
        ORDER BY created_at DESC
        """,
        (payer_id,),
    ).fetchall()


# ============================================================
# DEVICE HASH
# ============================================================

def make_device_hash(
    device_id: Optional[str],
    user_agent: str,
) -> str:

    raw = (
        device_id
        or user_agent
        or "unknown-device"
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


# ============================================================
# AMOUNT DEVIATION
# ============================================================

def calculate_amount_deviation(
    amount: float,
    history: List[sqlite3.Row],
) -> float:

    # --------------------------------------------------------
    # IMPORTANT:
    # No amount anomaly for <= ₹1000.
    # --------------------------------------------------------

    if amount <= 1000:

        return 0.0


    successful_amounts = [

        float(row["amount"])

        for row in history

        if (
            str(row["status"]).upper()
            == "SUCCESS"
        )

        and

        float(row["amount"]) > 0
    ]


    # No historical evidence = no user-specific
    # amount anomaly.
    if not successful_amounts:

        return 0.0


    successful_amounts.sort()


    middle = len(
        successful_amounts
    ) // 2


    if len(successful_amounts) % 2:

        median = successful_amounts[
            middle
        ]

    else:

        median = (
            successful_amounts[
                middle - 1
            ]
            +
            successful_amounts[
                middle
            ]
        ) / 2


    if median <= 0:

        return 0.0


    deviation = (
        amount / median
    ) - 1.0


    return min(
        max(
            0.0,
            deviation,
        ),
        10.0,
    )


# ============================================================
# CALCULATE 8 BEHAVIORAL SIGNALS
# ============================================================

def calculate_signals(
    conn: sqlite3.Connection,
    payer: sqlite3.Row,
    amount: float,
    recipient_upi_id: str,
    device_id: Optional[str],
    location: Optional[str],
    user_agent: str,
) -> Dict[str, bool]:

    payer_id = payer["user_id"]


    history = get_history(
        conn,
        payer_id,
    )


    successful = [

        row

        for row in history

        if (
            str(row["status"]).upper()
            == "SUCCESS"
        )
    ]


    # ========================================================
    # 1. TIME ANOMALY
    # ========================================================

    current_hour = datetime.now().hour

    historical_hours = []


    for row in successful:

        try:

            date_value = datetime.fromisoformat(
                str(
                    row["created_at"]
                ).replace(
                    "Z",
                    "+00:00",
                )
            )

            historical_hours.append(
                date_value.astimezone().hour
            )

        except Exception:

            pass


    time_anomaly = False


    if historical_hours:

        time_anomaly = not any(

            (
                abs(
                    current_hour - hour
                )
                <= 3
            )

            or

            (
                abs(
                    current_hour - hour
                )
                >= 21
            )

            for hour
            in historical_hours
        )


    # ========================================================
    # 2. TRANSACTION FREQUENCY
    # ========================================================

    cutoff = (
        datetime.now(timezone.utc)
        -
        timedelta(hours=24)
    )


    recent_count = 0


    for row in history:

        try:

            transaction_time = datetime.fromisoformat(
                str(
                    row["created_at"]
                ).replace(
                    "Z",
                    "+00:00",
                )
            )


            if (
                transaction_time >= cutoff
                and
                str(
                    row["status"]
                ).upper()
                == "SUCCESS"
            ):

                recent_count += 1

        except Exception:

            pass


    transaction_frequency = (
        recent_count >= 4
    )


    # ========================================================
    # 3. NEW DEVICE
    # ========================================================

    current_device_hash = make_device_hash(
        device_id,
        user_agent,
    )


    known_device = conn.execute(
        """
        SELECT 1
        FROM devices
        WHERE payer_id=?
        AND device_hash=?
        """,
        (
            payer_id,
            current_device_hash,
        ),
    ).fetchone()


    new_device = (
        known_device is None
    )


    now = utc_now()


    conn.execute(
        """
        INSERT INTO devices
        (
            payer_id,
            device_hash,
            first_seen,
            last_seen
        )
        VALUES (?, ?, ?, ?)

        ON CONFLICT(
            payer_id,
            device_hash
        )

        DO UPDATE SET
            last_seen=excluded.last_seen
        """,
        (
            payer_id,
            current_device_hash,
            now,
            now,
        ),
    )


    # ========================================================
    # 4 / 5. LOCATION
    # ========================================================

    unusual_location = False

    sudden_location_change = False


    if location:

        current_location = normalize(
            location
        )


        previous_location = conn.execute(
            """
            SELECT last_location
            FROM locations
            WHERE payer_id=?
            """,
            (payer_id,),
        ).fetchone()


        if (
            previous_location
            and
            previous_location["last_location"]
        ):

            old_location = normalize(
                previous_location[
                    "last_location"
                ]
            )


            if (
                current_location
                != old_location
            ):

                unusual_location = True

                sudden_location_change = True


        conn.execute(
            """
            INSERT INTO locations
            (
                payer_id,
                last_location,
                last_seen
            )
            VALUES (?, ?, ?)

            ON CONFLICT(payer_id)

            DO UPDATE SET
                last_location=excluded.last_location,
                last_seen=excluded.last_seen
            """,
            (
                payer_id,
                location,
                now,
            ),
        )


    # ========================================================
    # 6 / 7. BENEFICIARY / PREVIOUS TRANSACTION
    # ========================================================

    recipient_normalized = normalize(
        recipient_upi_id
    )


    known_recipient = any(

        normalize(
            row["recipient_upi_id"]
        )
        ==
        recipient_normalized

        for row in successful
    )


    unknown_beneficiary = (
        not known_recipient
    )


    # The risk factor is active when there is NO
    # previous payment to this recipient.
    previous_transaction = (
        not known_recipient
    )


    # ========================================================
    # 8. TYPICAL AMOUNT
    # ========================================================

    amount_deviation = calculate_amount_deviation(
        amount,
        history,
    )


    typical_amount = (
        amount_deviation > 0.50
    )


    # ========================================================
    # EXACTLY EIGHT SWITCHES
    # ========================================================

    return {

        "time_anomaly":
            time_anomaly,

        "transaction_frequency":
            transaction_frequency,

        "new_device":
            new_device,

        "unusual_location":
            unusual_location,

        "sudden_location_change":
            sudden_location_change,

        "unknown_beneficiary":
            unknown_beneficiary,

        "previous_transaction":
            previous_transaction,

        "typical_amount":
            typical_amount,
    }


# ============================================================
# ML MODEL
# ============================================================

def train_ml_model():

    if RandomForestRegressor is None:

        return None


    rng = random.Random(
        20260821
    )


    X = []

    y = []


    weight_values = list(
        RISK_WEIGHTS.values()
    )


    for _ in range(2500):

        eight_signals = [

            rng.randint(0, 1)

            for _ in RISK_WEIGHTS
        ]


        amount_deviation = (
            rng.random()
            * 3.0
        )


        weighted_score = sum(

            eight_signals[index]
            *
            weight_values[index]

            for index
            in range(
                len(eight_signals)
            )
        )


        amount_points = 0.0


        if amount_deviation > 0:

            amount_points = min(

                AMOUNT_WEIGHT,

                amount_deviation
                *
                AMOUNT_WEIGHT,
            )


        target = min(

            100.0,

            weighted_score
            +
            amount_points,
        )


        # Small training noise prevents the model from merely
        # being a hard-coded formula.
        target = max(

            0.0,

            min(

                100.0,

                target
                +
                rng.uniform(
                    -1.5,
                    1.5,
                ),
            ),
        )


        X.append(
            eight_signals
            +
            [amount_deviation]
        )


        y.append(target)


    model = RandomForestRegressor(

        n_estimators=120,

        max_depth=8,

        random_state=42,

        n_jobs=-1,
    )


    model.fit(
        X,
        y,
    )


    return model


MODEL = train_ml_model()


# ============================================================
# PREDICT RISK
# ============================================================

def predict_risk(
    signals: Dict[str, bool],
    amount_deviation: float,
) -> int:

    features = [

        int(
            signals[
                key
            ]
        )

        for key
        in RISK_WEIGHTS

    ]


    features.append(
        amount_deviation
    )


    if MODEL is not None:

        score = float(
            MODEL.predict(
                [features]
            )[0]
        )

    else:

        score = sum(

            RISK_WEIGHTS[key]

            for key, active
            in signals.items()

            if active
        )


        if amount_deviation > 0:

            score += min(

                AMOUNT_WEIGHT,

                amount_deviation
                *
                AMOUNT_WEIGHT,
            )


    return max(
        0,
        min(
            100,
            int(
                round(score)
            ),
        ),
    )


# ============================================================
# SELECT DYNAMIC QUESTION
# ============================================================

def select_dynamic_question(
    conn: sqlite3.Connection,
    payer_id: str,
    signals: Dict[str, bool],
) -> sqlite3.Row:

    candidate_codes = []


    # Prioritize questions related to the detected
    # behavioral anomalies.

    for factor, active in signals.items():

        if active:

            candidate_codes.extend(
                QUESTION_PRIORITY.get(
                    factor,
                    [],
                )
            )


    # Fallback questions.
    if not candidate_codes:

        candidate_codes = [

            "RECIPIENT_CONFIRM",

            "HISTORY_CONFIRM",

            "DEVICE_CONFIRM",

            "COLLEGE_CONFIRM",
        ]


    # Remove duplicates while keeping order.
    candidate_codes = list(
        dict.fromkeys(
            candidate_codes
        )
    )


    placeholders = ",".join(
        "?"
        *
        len(candidate_codes)
    )


    parameters = [
        payer_id,
        *candidate_codes,
    ]


    rows = conn.execute(
        f"""
        SELECT *
        FROM dynamic_question_data
        WHERE user_id=?
        AND question_code IN (
            {placeholders}
        )
        """,
        parameters,
    ).fetchall()


    if not rows:

        raise HTTPException(
            status_code=500,
            detail=(
                "No dynamic questions are "
                "configured for this payer."
            ),
        )


    # Avoid immediately repeating the same question.
    last_question = conn.execute(
        """
        SELECT question_code
        FROM challenges
        WHERE payer_id=?
        ORDER BY expires_at DESC
        LIMIT 1
        """,
        (payer_id,),
    ).fetchone()


    filtered = [

        row

        for row in rows

        if (
            not last_question
            or
            row["question_code"]
            !=
            last_question[
                "question_code"
            ]
        )
    ]


    pool = (
        filtered
        if filtered
        else rows
    )


    return secrets.choice(
        pool
    )


# ============================================================
# API MODELS
# ============================================================

class AnalyzeRequest(BaseModel):

    payer_id: str

    recipient_name: str = Field(
        min_length=1
    )

    recipient_upi_id: str = Field(
        min_length=1
    )

    amount: float = Field(
        gt=0
    )

    # Optional context used by the risk engine.
    device_id: Optional[str] = None

    location: Optional[str] = None

    # These are accepted for frontend compatibility.
    # The backend recalculates them and never trusts the
    # frontend's risk result.

    time_anomaly: Optional[bool] = None

    transaction_frequency: Optional[bool] = None

    new_device: Optional[bool] = None

    unusual_location: Optional[bool] = None

    sudden_location_change: Optional[bool] = None

    unknown_beneficiary: Optional[bool] = None

    previous_transaction: Optional[bool] = None

    typical_amount: Optional[bool] = None


class VerifyRequest(BaseModel):

    challenge_id: str

    answer: str = Field(
        min_length=1
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    conn = get_conn()

    try:

        payee_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM payees
            """
        ).fetchone()[0]


        return {

            "status": "ok",

            "database":
                DB_PATH.name,

            "payees":
                payee_count,

            "ml_model":
                MODEL is not None,

            "risk_bands": {

                "allow":
                    "0-49",

                "verify":
                    "50-79",

                "block":
                    "80-100",
            },
        }

    finally:

        conn.close()


# ============================================================
# USERS / PAYEES
# ============================================================

@app.get("/users")
def users():

    conn = get_conn()

    try:

        rows = conn.execute(
            """
            SELECT
                user_id,
                name,
                balance,
                upi_id
            FROM payees
            ORDER BY user_id
            """
        ).fetchall()


        return {

            "users": [

                row_to_dict(row)

                for row
                in rows
            ]
        }

    finally:

        conn.close()


# ============================================================
# TRANSACTIONS
# ============================================================

@app.get(
    "/transactions/{payer_id}"
)
def transactions(
    payer_id: str,
):

    conn = get_conn()

    try:

        get_payer(
            conn,
            payer_id,
        )


        rows = get_history(
            conn,
            payer_id,
        )


        return {

            "transactions": [

                row_to_dict(row)

                for row
                in rows
            ]
        }

    finally:

        conn.close()


# ============================================================
# ANALYZE PAYMENT
# ============================================================

@app.post(
    "/analyze-payment"
)
def analyze_payment(
    payload: AnalyzeRequest,
):

    conn = get_conn()

    try:

        payer = get_payer(
            conn,
            payload.payer_id,
        )


        # ====================================================
        # BALANCE CHECK
        # ====================================================
        #
        # Balance is NOT deducted.
        #
        # It is ONLY checked so the system can reject a
        # payment larger than the payer's available balance.
        # ====================================================

        if (
            payload.amount
            >
            float(
                payer["balance"]
            )
        ):

            transaction_id = (
                "TX-"
                +
                secrets.token_hex(
                    6
                ).upper()
            )


            conn.execute(
                """
                INSERT INTO transactions
                (
                    transaction_id,
                    payer_id,
                    recipient_name,
                    recipient_upi_id,
                    amount,
                    risk_score,
                    decision,
                    status,
                    signals_json,
                    amount_deviation,
                    created_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    transaction_id,

                    payload.payer_id,

                    payload.recipient_name.strip(),

                    payload.recipient_upi_id.strip(),

                    payload.amount,

                    None,

                    "INSUFFICIENT_BALANCE",

                    "FAILED",

                    "{}",

                    0.0,

                    utc_now(),
                ),
            )


            conn.commit()


            return {

                "success": False,

                "status":
                    "INSUFFICIENT_BALANCE",

                "decision":
                    "INSUFFICIENT_BALANCE",

                "message":
                    "Insufficient balance.",

                "transaction_id":
                    transaction_id,

                "payer_id":
                    payload.payer_id,

                "recipient_name":
                    payload.recipient_name,

                "recipient_upi_id":
                    payload.recipient_upi_id,

                "amount":
                    payload.amount,

                "available_balance":
                    payer["balance"],
            }


        # ====================================================
        # CALCULATE THE 8 SIGNALS
        # ====================================================

        user_agent = ""

        signals = calculate_signals(

            conn,

            payer,

            payload.amount,

            payload.recipient_upi_id,

            payload.device_id,

            payload.location,

            user_agent,
        )


        # ====================================================
        # INTERNAL AMOUNT DEVIATION
        # ====================================================

        amount_deviation = (
            calculate_amount_deviation(

                payload.amount,

                get_history(
                    conn,
                    payload.payer_id,
                ),
            )
        )


        # ====================================================
        # ML RISK SCORE
        # ====================================================

        risk_score = predict_risk(

            signals,

            amount_deviation,
        )


        # ====================================================
        # TRANSACTION ID
        # ====================================================

        transaction_id = (
            "TX-"
            +
            secrets.token_hex(
                6
            ).upper()
        )


        # ====================================================
        # RISK DECISION
        # ====================================================

        if risk_score >= 80:

            decision = "BLOCK"

            status = "BLOCKED"


        elif risk_score >= 50:

            decision = "HOLD"

            status = "PENDING_AUTH"


        else:

            decision = "ALLOW"

            status = "SUCCESS"


        # ====================================================
        # SAVE TRANSACTION
        # ====================================================

        conn.execute(
            """
            INSERT INTO transactions
            (
                transaction_id,
                payer_id,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                decision,
                status,
                signals_json,
                amount_deviation,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,
            (
                transaction_id,

                payload.payer_id,

                payload.recipient_name.strip(),

                payload.recipient_upi_id.strip(),

                payload.amount,

                risk_score,

                decision,

                status,

                json.dumps(
                    signals
                ),

                amount_deviation,

                utc_now(),
            ),
        )


        response = {

            "success":
                decision == "ALLOW",

            "transaction_id":
                transaction_id,

            "payer_id":
                payload.payer_id,

            "recipient_name":
                payload.recipient_name,

            "recipient_upi_id":
                payload.recipient_upi_id,

            "amount":
                payload.amount,

            "risk_score":
                risk_score,

            "decision":
                decision,

            "status":
                status,

            "signals":
                signals,

            "amount_deviation":
                round(
                    amount_deviation,
                    4,
                ),

            "available_balance":
                payer["balance"],

            # Balance intentionally unchanged.
            "new_balance":
                payer["balance"],

            "model_used":
                (
                    "RandomForestRegressor"
                    if MODEL is not None
                    else "WeightedFallback"
                ),
        }


        # ====================================================
        # 80+ = INSECURE TRANSACTION
        # ====================================================

        if decision == "BLOCK":

            response["message"] = (
                "Transaction marked as insecure "
                "because the risk score is 80 or above."
            )


        # ====================================================
        # 0-49 = ALLOW
        # ====================================================

        elif decision == "ALLOW":

            response["message"] = (
                "Transaction approved. "
                "Balance was not deducted."
            )


        # ====================================================
        # 50-79 = DYNAMIC AUTHENTICATION
        # ====================================================

        else:

            question = select_dynamic_question(

                conn,

                payload.payer_id,

                signals,
            )


            challenge_id = (
                "CH-"
                +
                secrets.token_hex(
                    8
                ).upper()
            )


            expires_at = (
                datetime.now(
                    timezone.utc
                )
                +
                timedelta(
                    minutes=5
                )
            ).isoformat()


            # =================================================
            # EXPECTED ANSWER NEVER GOES TO FRONTEND
            # =================================================

            conn.execute(
                """
                INSERT INTO challenges
                (
                    challenge_id,
                    transaction_id,
                    payer_id,
                    question_id,
                    question_code,
                    question_text,
                    expected_answer_type,
                    expected_answer,
                    expires_at,
                    used
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, 0
                )
                """,
                (
                    challenge_id,

                    transaction_id,

                    payload.payer_id,

                    question["question_id"],

                    question["question_code"],

                    question["question_text"],

                    question[
                        "expected_answer_type"
                    ],

                    question[
                        "expected_answer"
                    ],

                    expires_at,
                ),
            )


            response["message"] = (
                "Risk is in the verification range. "
                "Complete the dynamic authentication question."
            )


            response["challenge"] = {

                "challenge_id":
                    challenge_id,

                "question":
                    question[
                        "question_text"
                    ],

                "answer_type":
                    question[
                        "expected_answer_type"
                    ],
            }


        conn.commit()


        return response


    finally:

        conn.close()


# ============================================================
# VERIFY DYNAMIC QUESTION
# ============================================================

@app.post(
    "/verify-challenge"
)
def verify_challenge(
    payload: VerifyRequest,
):

    conn = get_conn()

    try:

        challenge = conn.execute(
            """
            SELECT *
            FROM challenges
            WHERE challenge_id=?
            """,
            (
                payload.challenge_id,
            ),
        ).fetchone()


        if not challenge:

            raise HTTPException(

                status_code=404,

                detail:
                    "Authentication challenge not found.",
            )


        # ====================================================
        # CHALLENGE ALREADY USED
        # ====================================================

        if int(
            challenge["used"]
        ) == 1:

            return {

                "success": False,

                "status":
                    "FAILED",

                "decision":
                    "FAILED",

                "message":
                    "This authentication challenge has already been used.",
            }


        # ====================================================
        # CHALLENGE EXPIRATION
        # ====================================================

        expires_at = datetime.fromisoformat(

            str(
                challenge[
                    "expires_at"
                ]
            ).replace(
                "Z",
                "+00:00",
            )
        )


        if (
            datetime.now(
                timezone.utc
            )
            >
            expires_at
        ):

            conn.execute(
                """
                UPDATE challenges
                SET used=1
                WHERE challenge_id=?
                """,
                (
                    payload.challenge_id,
                ),
            )


            conn.execute(
                """
                UPDATE transactions
                SET
                    status='FAILED',
                    decision='FAILED'
                WHERE transaction_id=?
                """,
                (
                    challenge[
                        "transaction_id"
                    ],
                ),
            )


            conn.commit()


            return {

                "success": False,

                "status":
                    "FAILED",

                "decision":
                    "FAILED",

                "message":
                    "Authentication challenge expired. Payment failed.",
            }


        # ====================================================
        # CHECK ANSWER
        # ====================================================

        correct = answer_matches(

            challenge[
                "expected_answer"
            ],

            payload.answer,

            challenge[
                "expected_answer_type"
            ],
        )


        # ====================================================
        # ONE-TIME CHALLENGE
        # ====================================================

        conn.execute(
            """
            UPDATE challenges
            SET used=1
            WHERE challenge_id=?
            """,
            (
                payload.challenge_id,
            ),
        )


        transaction = conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE transaction_id=?
            """,
            (
                challenge[
                    "transaction_id"
                ],
            ),
        ).fetchone()


        if not transaction:

            conn.commit()

            raise HTTPException(

                status_code=404,

                detail:
                    "Transaction not found.",
            )


        # ====================================================
        # WRONG ANSWER
        # ====================================================

        if not correct:

            conn.execute(
                """
                UPDATE transactions

                SET
                    status='FAILED',
                    decision='FAILED'

                WHERE transaction_id=?
                """,
                (
                    challenge[
                        "transaction_id"
                    ],
                ),
            )


            conn.commit()


            return {

                "success":
                    False,

                "status":
                    "FAILED",

                "decision":
                    "FAILED",

                "message":
                    "Incorrect answer. Payment failed.",

                "transaction_id":
                    transaction[
                        "transaction_id"
                    ],

                "payer_id":
                    transaction[
                        "payer_id"
                    ],

                "recipient_name":
                    transaction[
                        "recipient_name"
                    ],

                "recipient_upi_id":
                    transaction[
                        "recipient_upi_id"
                    ],

                "amount":
                    transaction[
                        "amount"
                    ],

                "risk_score":
                    transaction[
                        "risk_score"
                    ],
            }


        # ====================================================
        # CORRECT ANSWER
        # ====================================================
        #
        # IMPORTANT:
        # Balance is NOT deducted.
        # ====================================================

        conn.execute(
            """
            UPDATE transactions

            SET
                status='SUCCESS',
                decision='ALLOW'

            WHERE transaction_id=?
            """,
            (
                challenge[
                    "transaction_id"
                ],
            ),
        )


        payer = get_payer(

            conn,

            transaction[
                "payer_id"
            ],
        )


        signals = {}

        if transaction[
            "signals_json"
        ]:

            try:

                signals = json.loads(
                    transaction[
                        "signals_json"
                    ]
                )

            except Exception:

                signals = {}


        conn.commit()


        return {

            "success":
                True,

            "status":
                "SUCCESS",

            "decision":
                "ALLOW",

            "message":
                "Verification successful. Payment completed.",

            "transaction_id":
                transaction[
                    "transaction_id"
                ],

            "payer_id":
                transaction[
                    "payer_id"
                ],

            "recipient_name":
                transaction[
                    "recipient_name"
                ],

            "recipient_upi_id":
                transaction[
                    "recipient_upi_id"
                ],

            "amount":
                transaction[
                    "amount"
                ],

            "risk_score":
                transaction[
                    "risk_score"
                ],

            "signals":
                signals,

            "available_balance":
                payer[
                    "balance"
                ],

            "new_balance":
                payer[
                    "balance"
                ],

            "model_used":
                (
                    "RandomForestRegressor"
                    if MODEL is not None
                    else "WeightedFallback"
                ),
        }


    finally:

        conn.close()


# ============================================================
# RESET DASHBOARD
# ============================================================

@app.post(
    "/reset-dashboard"
)
def reset_dashboard():

    conn = get_conn()

    try:

        # Delete transaction-specific data.
        conn.execute(
            "DELETE FROM challenges"
        )

        conn.execute(
            "DELETE FROM transactions"
        )

        conn.execute(
            "DELETE FROM devices"
        )

        conn.execute(
            "DELETE FROM locations"
        )


        # Restore original balances.
        conn.execute(
            """
            UPDATE payees

            SET balance =
                CASE user_id

                    WHEN 'U001'
                    THEN 55000

                    WHEN 'U002'
                    THEN 60000

                    WHEN 'U003'
                    THEN 50000

                    WHEN 'U004'
                    THEN 40000

                END
            """
        )


        conn.commit()


        return {

            "success":
                True,

            "message":
                "Dashboard reset. All four payer balances were restored.",
        }


    finally:

        conn.close()


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn


    uvicorn.run(

        app,

        host="0.0.0.0",

        port=8000,

        reload=False,
    )
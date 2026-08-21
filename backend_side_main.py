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
DB_PATH = BASE_DIR / "SecureFlow-AI8.db"

app = FastAPI(
    title="SecureFlow AI Risk Engine",
    version="2.0.0",
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
# PAPER:
#
# 1. Amount                -> INTERNAL ONLY
# 2. Time                  -> 7
# 3. Frequency             -> 12
# 4. New Device            -> 15
# 5. Unusual Location      -> 15
# 6. Sudden Location       -> 6
# 7. Unknown Beneficiary   -> 12
# 8. Previous Transaction  -> 13
# 9. Typical Amount        -> 10
#
# Amount is NOT shown as a checkbox.
# Therefore exactly 8 switches are returned to the dashboard.
#
# Maximum:
# 7 + 12 + 15 + 15 + 6 + 12 + 13 + 10 = 90
# Amount contributes up to 10 internally.
#
# Total maximum = 100.
# ============================================================

RISK_WEIGHTS: Dict[str, int] = {
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
# FOUR PAYERS
# ============================================================

DEFAULT_PAYEES = [
    {
        "user_id": "U001",
        "name": "Soumadip Das",
        "balance": 55000.0,
        "upi_id": "soumadip@upi",
    },
    {
        "user_id": "U002",
        "name": "Shubham Paul",
        "balance": 60000.0,
        "upi_id": "shubham.paul@upi",
    },
    {
        "user_id": "U003",
        "name": "Shubham Mukherjee",
        "balance": 50000.0,
        "upi_id": "shubham.mukherjee@upi",
    },
    {
        "user_id": "U004",
        "name": "Tridip Debroy",
        "balance": 40000.0,
        "upi_id": "tridip.debroy@upi",
    },
]


# ============================================================
# DYNAMIC QUESTION PRIORITY
# ============================================================

QUESTION_PRIORITY: Dict[str, List[str]] = {
    "new_device": [
        "DEVICE_CONFIRM",
    ],
    "unusual_location": [
        "LOCATION_CONFIRM",
        "AREA_CONFIRM",
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
        "DOB_CONFIRM",
        "COLLEGE_CONFIRM",
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
        str(value or "").strip().casefold().split()
    )


def answer_matches(
    expected: str,
    actual: str,
    answer_type: str,
) -> bool:
    expected_normalized = normalize(expected)
    actual_normalized = normalize(actual)

    if answer_type == "YES_NO":
        expected_yes = expected_normalized in {"yes", "y"}
        actual_yes = actual_normalized in {"yes", "y"}

        expected_no = expected_normalized in {"no", "n"}
        actual_no = actual_normalized in {"no", "n"}

        return (expected_yes and actual_yes) or (
            expected_no and actual_no
        )

    return expected_normalized == actual_normalized


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    return conn


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row)


def safe_json(value: Any) -> str:
    try:
        return json.dumps(value)
    except Exception:
        return "{}"


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
                PRIMARY KEY (payer_id, device_hash)
            );

            CREATE TABLE IF NOT EXISTS locations (
                payer_id TEXT PRIMARY KEY,
                last_location TEXT,
                last_seen TEXT NOT NULL
            );
            """
        )

        # ------------------------------------------------------
        # Ensure the four required payers exist.
        # ------------------------------------------------------

        for payer in DEFAULT_PAYEES:
            conn.execute(
                """
                INSERT INTO payees
                (
                    user_id,
                    name,
                    balance,
                    upi_id
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    name=excluded.name,
                    upi_id=excluded.upi_id
                """,
                (
                    payer["user_id"],
                    payer["name"],
                    payer["balance"],
                    payer["upi_id"],
                ),
            )

        # ------------------------------------------------------
        # Dynamic questions from supplied database screenshots.
        #
        # AMOUNT_CONFIRM is intentionally excluded.
        # ------------------------------------------------------

        questions = [
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
            INSERT INTO dynamic_question_data
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
            ON CONFLICT(user_id, question_code)
            DO UPDATE SET
                name=excluded.name,
                question_id=excluded.question_id,
                question_text=excluded.question_text,
                risk_factor=excluded.risk_factor,
                expected_answer_type=excluded.expected_answer_type,
                expected_answer=excluded.expected_answer
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
        SELECT
            user_id,
            name,
            balance,
            upi_id
        FROM payees
        WHERE user_id=?
        """,
        (payer_id,),
    ).fetchone()

    if row is None:
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


def make_transaction_id() -> str:
    return "TX-" + secrets.token_hex(6).upper()


def make_challenge_id() -> str:
    return "CH-" + secrets.token_hex(8).upper()


# ============================================================
# DEVICE HASH
# ============================================================

def make_device_hash(
    device_id: Optional[str],
    user_agent: str,
) -> str:
    raw = (
        device_id.strip()
        if device_id and device_id.strip()
        else user_agent.strip()
        if user_agent and user_agent.strip()
        else "unknown-device"
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
    """
    Amount is completely ignored for <= ₹1000.

    For > ₹1000:
    compare against this payer's successful historical
    transaction amounts.

    Returns a ratio:
        0.0  = normal/no evidence
        0.5  = 50% above historical median
        1.0  = 100% above historical median
        etc.

    The ratio is capped at 10.
    """

    if amount <= 1000:
        return 0.0

    historical_amounts = []

    for row in history:
        if str(row["status"]).upper() != "SUCCESS":
            continue

        try:
            value = float(row["amount"])
        except (TypeError, ValueError):
            continue

        if value > 0:
            historical_amounts.append(value)

    if not historical_amounts:
        return 0.0

    historical_amounts.sort()

    count = len(historical_amounts)
    middle = count // 2

    if count % 2 == 1:
        median = historical_amounts[middle]
    else:
        median = (
            historical_amounts[middle - 1]
            + historical_amounts[middle]
        ) / 2.0

    if median <= 0:
        return 0.0

    deviation = (amount / median) - 1.0

    return max(
        0.0,
        min(deviation, 10.0),
    )


# ============================================================
# PARSE TRANSACTION DATE
# ============================================================

def parse_datetime(value: Any) -> Optional[datetime]:
    try:
        text = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed
    except Exception:
        return None


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

    payer_id = str(payer["user_id"])

    history = get_history(
        conn,
        payer_id,
    )

    successful = [
        row
        for row in history
        if str(row["status"]).upper() == "SUCCESS"
    ]

    # --------------------------------------------------------
    # 1. TIME ANOMALY
    # --------------------------------------------------------

    now_local = datetime.now().astimezone()
    current_hour = now_local.hour

    historical_hours: List[int] = []

    for row in successful:
        parsed = parse_datetime(row["created_at"])

        if parsed is not None:
            historical_hours.append(
                parsed.astimezone().hour
            )

    time_anomaly = False

    if historical_hours:
        close_to_normal_time = any(
            (
                abs(current_hour - hour) <= 3
                or abs(current_hour - hour) >= 21
            )
            for hour in historical_hours
        )

        time_anomaly = not close_to_normal_time

    # --------------------------------------------------------
    # 2. TRANSACTION FREQUENCY
    # --------------------------------------------------------

    cutoff = (
        datetime.now(timezone.utc)
        - timedelta(hours=24)
    )

    recent_count = 0

    for row in successful:
        parsed = parse_datetime(row["created_at"])

        if parsed is not None and parsed >= cutoff:
            recent_count += 1

    transaction_frequency = recent_count >= 4

    # --------------------------------------------------------
    # 3. NEW DEVICE
    # --------------------------------------------------------

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

    new_device = known_device is None

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
        ON CONFLICT(payer_id, device_hash)
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

    # --------------------------------------------------------
    # 4. UNUSUAL LOCATION
    # --------------------------------------------------------

    unusual_location = False
    sudden_location_change = False

    if location and location.strip():

        current_location = normalize(location)

        previous = conn.execute(
            """
            SELECT last_location
            FROM locations
            WHERE payer_id=?
            """,
            (payer_id,),
        ).fetchone()

        if previous is not None:
            previous_location = normalize(
                previous["last_location"]
            )

            if (
                previous_location
                and current_location != previous_location
            ):
                sudden_location_change = True

        # Determine unusual location from the payer's
        # configured normal location question.

        normal_location_row = conn.execute(
            """
            SELECT expected_answer
            FROM dynamic_question_data
            WHERE user_id=?
            AND question_code='LOCATION_CONFIRM'
            LIMIT 1
            """,
            (payer_id,),
        ).fetchone()

        if normal_location_row is not None:
            normal_location = normalize(
                normal_location_row["expected_answer"]
            )

            if (
                normal_location
                and current_location != normal_location
            ):
                unusual_location = True

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
                location.strip(),
                now,
            ),
        )

    # --------------------------------------------------------
    # 5 / 6. RECIPIENT / PREVIOUS TRANSACTION
    # --------------------------------------------------------

    recipient_normalized = normalize(
        recipient_upi_id
    )

    known_recipient = False

    for row in successful:
        previous_recipient = normalize(
            row["recipient_upi_id"]
        )

        if previous_recipient == recipient_normalized:
            known_recipient = True
            break

    unknown_beneficiary = not known_recipient

    # Paper factor is treated as a risk signal when the
    # recipient has NOT appeared in successful history.
    previous_transaction = not known_recipient

    # --------------------------------------------------------
    # 7. TYPICAL AMOUNT
    # --------------------------------------------------------

    amount_deviation = calculate_amount_deviation(
        amount,
        history,
    )

    typical_amount = (
        amount > 1000
        and amount_deviation > 0.50
    )

    # --------------------------------------------------------
    # EXACTLY 8 SIGNALS
    # --------------------------------------------------------

    return {
        "time_anomaly": bool(time_anomaly),
        "transaction_frequency": bool(
            transaction_frequency
        ),
        "new_device": bool(new_device),
        "unusual_location": bool(
            unusual_location
        ),
        "sudden_location_change": bool(
            sudden_location_change
        ),
        "unknown_beneficiary": bool(
            unknown_beneficiary
        ),
        "previous_transaction": bool(
            previous_transaction
        ),
        "typical_amount": bool(
            typical_amount
        ),
    }


# ============================================================
# ML MODEL
# ============================================================

def train_ml_model():
    """
    Train a reproducible Random Forest using the paper's
    weighting system.

    The model receives:
        8 behavioral switches
        + internal amount deviation

    The model output is constrained to 0-100.
    """

    if RandomForestRegressor is None:
        return None

    rng = random.Random(20260821)

    X: List[List[float]] = []
    y: List[float] = []

    weight_values = list(
        RISK_WEIGHTS.values()
    )

    for _ in range(3000):

        switches = [
            rng.randint(0, 1)
            for _ in RISK_WEIGHTS
        ]

        amount_deviation = rng.uniform(
            0.0,
            3.0,
        )

        behavioral_score = sum(
            switches[index] * weight_values[index]
            for index in range(len(switches))
        )

        amount_points = min(
            AMOUNT_WEIGHT,
            amount_deviation * AMOUNT_WEIGHT,
        )

        target = min(
            100.0,
            behavioral_score + amount_points,
        )

        X.append(
            switches + [amount_deviation]
        )

        y.append(target)

    model = RandomForestRegressor(
        n_estimators=150,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X, y)

    return model


MODEL = train_ml_model()


# ============================================================
# PREDICT RISK
# ============================================================

def calculate_weighted_score(
    signals: Dict[str, bool],
    amount_deviation: float,
) -> int:

    score = 0

    for key, weight in RISK_WEIGHTS.items():
        if signals.get(key, False):
            score += weight

    if amount_deviation > 0:
        score += min(
            AMOUNT_WEIGHT,
            int(
                round(
                    amount_deviation
                    * AMOUNT_WEIGHT
                )
            ),
        )

    return max(
        0,
        min(100, score),
    )


def predict_risk(
    signals: Dict[str, bool],
    amount_deviation: float,
) -> int:

    features = [
        int(
            bool(
                signals.get(key, False)
            )
        )
        for key in RISK_WEIGHTS
    ]

    features.append(
        float(amount_deviation)
    )

    weighted_score = calculate_weighted_score(
        signals,
        amount_deviation,
    )

    if MODEL is None:
        return weighted_score

    try:
        prediction = float(
            MODEL.predict([features])[0]
        )

        # Keep the ML prediction close to the actual
        # paper scoring system.
        prediction = max(
            0.0,
            min(100.0, prediction),
        )

        return int(round(prediction))

    except Exception:
        return weighted_score


# ============================================================
# RISK BAND
# ============================================================

def get_risk_band(score: int) -> str:
    if score >= 80:
        return "HIGH"

    if score >= 50:
        return "MEDIUM"

    return "LOW"


# ============================================================
# SELECT DYNAMIC QUESTION
# ============================================================

def select_dynamic_question(
    conn: sqlite3.Connection,
    payer_id: str,
    signals: Dict[str, bool],
) -> sqlite3.Row:

    candidate_codes: List[str] = []

    # Highest priority comes from active signals.
    for factor, active in signals.items():
        if active:
            candidate_codes.extend(
                QUESTION_PRIORITY.get(
                    factor,
                    [],
                )
            )

    # Remove duplicates while preserving order.
    candidate_codes = list(
        dict.fromkeys(candidate_codes)
    )

    # If there are no anomaly-specific candidates,
    # use a safe fallback.
    if not candidate_codes:
        candidate_codes = [
            "RECIPIENT_CONFIRM",
            "HISTORY_CONFIRM",
            "DEVICE_CONFIRM",
            "AREA_CONFIRM",
            "LOCATION_CONFIRM",
            "NEARBY_PLACE_CONFIRM",
            "COLLEGE_CONFIRM",
            "DOB_CONFIRM",
        ]

    placeholders = ",".join(
        "?" for _ in candidate_codes
    )

    rows = conn.execute(
        f"""
        SELECT *
        FROM dynamic_question_data
        WHERE user_id=?
        AND question_code IN ({placeholders})
        ORDER BY id
        """,
        [
            payer_id,
            *candidate_codes,
        ],
    ).fetchall()

    if not rows:
        raise HTTPException(
            status_code=500,
            detail=(
                "No dynamic authentication "
                "questions exist for this payer."
            ),
        )

    # --------------------------------------------------------
    # Prevent the same question being repeatedly selected.
    # --------------------------------------------------------

    previous_challenges = conn.execute(
        """
        SELECT question_code
        FROM challenges
        WHERE payer_id=?
        ORDER BY rowid DESC
        LIMIT 10
        """,
        (payer_id,),
    ).fetchall()

    recently_used = {
        row["question_code"]
        for row in previous_challenges
    }

    fresh_rows = [
        row
        for row in rows
        if row["question_code"] not in recently_used
    ]

    if fresh_rows:
        rows = fresh_rows

    # Prefer the first priority candidate when possible.
    priority_index = {
        code: index
        for index, code
        in enumerate(candidate_codes)
    }

    rows = sorted(
        rows,
        key=lambda row: priority_index.get(
            row["question_code"],
            999,
        ),
    )

    # Select from the top priority group randomly so
    # repeated payments don't always ask exactly the same
    # question.
    top_priority = priority_index.get(
        rows[0]["question_code"],
        999,
    )

    top_rows = [
        row
        for row in rows
        if priority_index.get(
            row["question_code"],
            999,
        ) == top_priority
    ]

    return secrets.choice(top_rows)


# ============================================================
# API MODELS
# ============================================================

class AnalyzeRequest(BaseModel):
    payer_id: str = Field(
        min_length=1
    )

    recipient_name: str = Field(
        min_length=1
    )

    recipient_upi_id: str = Field(
        min_length=1
    )

    amount: float = Field(
        gt=0
    )

    device_id: Optional[str] = None

    location: Optional[str] = None

    # --------------------------------------------------------
    # These are accepted so the frontend can display
    # switches if required.
    #
    # THE BACKEND DOES NOT TRUST THEM.
    # The backend calculates every signal itself.
    # --------------------------------------------------------

    time_anomaly: Optional[bool] = None
    transaction_frequency: Optional[bool] = None
    new_device: Optional[bool] = None
    unusual_location: Optional[bool] = None
    sudden_location_change: Optional[bool] = None
    unknown_beneficiary: Optional[bool] = None
    previous_transaction: Optional[bool] = None
    typical_amount: Optional[bool] = None


class VerifyRequest(BaseModel):
    challenge_id: str = Field(
        min_length=1
    )

    answer: str = Field(
        min_length=1
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health() -> Dict[str, Any]:

    conn = get_conn()

    try:
        payee_count = conn.execute(
            "SELECT COUNT(*) FROM payees"
        ).fetchone()[0]

        question_count = conn.execute(
            "SELECT COUNT(*) FROM dynamic_question_data"
        ).fetchone()[0]

        transaction_count = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        return {
            "status": "ok",
            "database": DB_PATH.name,
            "database_path": str(DB_PATH),
            "payees": payee_count,
            "dynamic_questions": question_count,
            "transactions": transaction_count,
            "ml_model": MODEL is not None,
            "visible_risk_switches": 8,
            "amount_switch": False,
            "risk_bands": {
                "allow": "0-49",
                "verify": "50-79",
                "block": "80-100",
            },
        }

    finally:
        conn.close()


# ============================================================
# USERS / PAYERS
# ============================================================

@app.get("/users")
def users() -> Dict[str, Any]:

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
                for row in rows
            ]
        }

    finally:
        conn.close()


# ============================================================
# GET ONE PAYER
# ============================================================

@app.get("/users/{payer_id}")
def user_details(
    payer_id: str,
) -> Dict[str, Any]:

    conn = get_conn()

    try:
        payer = get_payer(
            conn,
            payer_id,
        )

        return {
            "user": row_to_dict(payer)
        }

    finally:
        conn.close()


# ============================================================
# TRANSACTION HISTORY
# ============================================================

@app.get("/transactions/{payer_id}")
def transactions(
    payer_id: str,
) -> Dict[str, Any]:

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
                for row in rows
            ]
        }

    finally:
        conn.close()


# ============================================================
# DYNAMIC QUESTIONS DEBUG/ADMIN ENDPOINT
# ============================================================
#
# This endpoint is useful for the hackathon demo.
# It DOES NOT expose expected answers.
# ============================================================

@app.get("/questions/{payer_id}")
def questions_for_payer(
    payer_id: str,
) -> Dict[str, Any]:

    conn = get_conn()

    try:
        get_payer(
            conn,
            payer_id,
        )

        rows = conn.execute(
            """
            SELECT
                question_id,
                question_code,
                question_text,
                risk_factor,
                expected_answer_type
            FROM dynamic_question_data
            WHERE user_id=?
            ORDER BY question_id
            """,
            (payer_id,),
        ).fetchall()

        return {
            "questions": [
                row_to_dict(row)
                for row in rows
            ]
        }

    finally:
        conn.close()


# ============================================================
# ANALYZE PAYMENT
# ============================================================

@app.post("/analyze-payment")
def analyze_payment(
    payload: AnalyzeRequest,
) -> Dict[str, Any]:

    conn = get_conn()

    try:
        payer = get_payer(
            conn,
            payload.payer_id,
        )

        payer_balance = float(
            payer["balance"]
        )

        amount = float(
            payload.amount
        )

        recipient_name = (
            payload.recipient_name.strip()
        )

        recipient_upi_id = (
            payload.recipient_upi_id.strip()
        )

        # ====================================================
        # BALANCE CHECK
        # ====================================================
        #
        # IMPORTANT:
        # No balance deduction.
        # Only check available balance.
        # ====================================================

        if amount > payer_balance:

            transaction_id = make_transaction_id()

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    payload.payer_id,
                    recipient_name,
                    recipient_upi_id,
                    amount,
                    None,
                    "INSUFFICIENT_BALANCE",
                    "FAILED",
                    safe_json({}),
                    0.0,
                    utc_now(),
                ),
            )

            conn.commit()

            return {
                "success": False,
                "status": "INSUFFICIENT_BALANCE",
                "decision": "INSUFFICIENT_BALANCE",
                "message": (
                    "Insufficient balance. "
                    "The payment amount exceeds "
                    "the payer's available balance."
                ),
                "transaction_id": transaction_id,
                "payer_id": payload.payer_id,
                "payer_name": payer["name"],
                "payer_upi_id": payer["upi_id"],
                "recipient_name": recipient_name,
                "recipient_upi_id": recipient_upi_id,
                "amount": amount,
                "available_balance": payer_balance,
                "new_balance": payer_balance,
                "risk_score": None,
            }

        # ====================================================
        # HISTORY BEFORE CURRENT TRANSACTION
        # ====================================================

        history_before = get_history(
            conn,
            payload.payer_id,
        )

        # ====================================================
        # CALCULATE THE 8 SIGNALS
        # ====================================================

        signals = calculate_signals(
            conn=conn,
            payer=payer,
            amount=amount,
            recipient_upi_id=recipient_upi_id,
            device_id=payload.device_id,
            location=payload.location,
            user_agent="",
        )

        # ====================================================
        # AMOUNT DEVIATION
        # ====================================================

        amount_deviation = calculate_amount_deviation(
            amount,
            history_before,
        )

        # ====================================================
        # ML RISK SCORE
        # ====================================================

        risk_score = predict_risk(
            signals,
            amount_deviation,
        )

        risk_band = get_risk_band(
            risk_score
        )

        # ====================================================
        # TRANSACTION ID
        # ====================================================

        transaction_id = make_transaction_id()

        # ====================================================
        # DECISION
        # ====================================================

        if risk_score >= 80:
            decision = "BLOCK"
            status = "INSECURE"

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
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                payload.payer_id,
                recipient_name,
                recipient_upi_id,
                amount,
                risk_score,
                decision,
                status,
                safe_json(signals),
                amount_deviation,
                utc_now(),
            ),
        )

        response: Dict[str, Any] = {
            "success": decision == "ALLOW",
            "transaction_id": transaction_id,
            "payer_id": payload.payer_id,
            "payer_name": payer["name"],
            "payer_upi_id": payer["upi_id"],
            "recipient_name": recipient_name,
            "recipient_upi_id": recipient_upi_id,
            "amount": amount,
            "risk_score": risk_score,
            "risk_band": risk_band,
            "decision": decision,
            "status": status,
            "signals": signals,
            "amount_deviation": round(
                amount_deviation,
                4,
            ),
            "available_balance": payer_balance,
            "new_balance": payer_balance,
            "balance_deducted": False,
            "model_used": (
                "RandomForestRegressor"
                if MODEL is not None
                else "WeightedFallback"
            ),
        }

        # ====================================================
        # HIGH RISK
        # ====================================================

        if risk_score >= 80:

            response["message"] = (
                "INSECURE TRANSACTION. "
                "Payment blocked because the "
                "risk score is 80 or above."
            )

        # ====================================================
        # LOW RISK
        # ====================================================

        elif risk_score < 50:

            response["message"] = (
                "Payment successful. "
                "Risk score is within the low-risk range."
            )

        # ====================================================
        # MEDIUM RISK
        # ====================================================

        else:

            question = select_dynamic_question(
                conn,
                payload.payer_id,
                signals,
            )

            challenge_id = make_challenge_id()

            expires_at = (
                datetime.now(timezone.utc)
                + timedelta(minutes=5)
            ).isoformat()

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
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    challenge_id,
                    transaction_id,
                    payload.payer_id,
                    question["question_id"],
                    question["question_code"],
                    question["question_text"],
                    question["expected_answer_type"],
                    question["expected_answer"],
                    expires_at,
                ),
            )

            response["message"] = (
                "Additional authentication required."
            )

            response["challenge"] = {
                "challenge_id": challenge_id,
                "question": question["question_text"],
                "answer_type": question[
                    "expected_answer_type"
                ],
                "question_code": question[
                    "question_code"
                ],
                "expires_at": expires_at,
            }

        conn.commit()

        return response

    except HTTPException:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Payment analysis failed: {exc}",
        )

    finally:
        conn.close()


# ============================================================
# VERIFY DYNAMIC QUESTION
# ============================================================

@app.post("/verify-challenge")
def verify_challenge(
    payload: VerifyRequest,
) -> Dict[str, Any]:

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

        if challenge is None:
            raise HTTPException(
                status_code=404,
                detail="Authentication challenge not found.",
            )

        # ====================================================
        # ALREADY USED
        # ====================================================

        if int(challenge["used"]) == 1:
            return {
                "success": False,
                "status": "FAILED",
                "decision": "FAILED",
                "message": (
                    "This authentication challenge "
                    "has already been used."
                ),
            }

        # ====================================================
        # EXPIRATION
        # ====================================================

        expires_at = parse_datetime(
            challenge["expires_at"]
        )

        if (
            expires_at is None
            or datetime.now(timezone.utc)
            > expires_at
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
                    challenge["transaction_id"],
                ),
            )

            conn.commit()

            return {
                "success": False,
                "status": "FAILED",
                "decision": "FAILED",
                "message": (
                    "Authentication challenge expired. "
                    "Payment failed."
                ),
            }

        # ====================================================
        # TRANSACTION
        # ====================================================

        transaction = conn.execute(
            """
            SELECT *
            FROM transactions
            WHERE transaction_id=?
            """,
            (
                challenge["transaction_id"],
            ),
        ).fetchone()

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found.",
            )

        # ====================================================
        # CHECK ANSWER
        # ====================================================

        correct = answer_matches(
            challenge["expected_answer"],
            payload.answer,
            challenge["expected_answer_type"],
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
                    challenge["transaction_id"],
                ),
            )

            conn.commit()

            return {
                "success": False,
                "status": "FAILED",
                "decision": "FAILED",
                "message": (
                    "Incorrect answer. "
                    "Payment failed."
                ),
                "transaction_id": transaction[
                    "transaction_id"
                ],
                "payer_id": transaction[
                    "payer_id"
                ],
                "recipient_name": transaction[
                    "recipient_name"
                ],
                "recipient_upi_id": transaction[
                    "recipient_upi_id"
                ],
                "amount": transaction[
                    "amount"
                ],
                "risk_score": transaction[
                    "risk_score"
                ],
                "balance_deducted": False,
            }

        # ====================================================
        # CORRECT ANSWER
        # ====================================================
        #
        # No balance deduction.
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
                challenge["transaction_id"],
            ),
        )

        payer = get_payer(
            conn,
            transaction["payer_id"],
        )

        signals: Dict[str, bool] = {}

        try:
            signals = json.loads(
                transaction["signals_json"]
                or "{}"
            )
        except Exception:
            signals = {}

        conn.commit()

        return {
            "success": True,
            "status": "SUCCESS",
            "decision": "ALLOW",
            "message": (
                "Verification successful. "
                "Payment completed."
            ),
            "transaction_id": transaction[
                "transaction_id"
            ],
            "payer_id": transaction[
                "payer_id"
            ],
            "payer_name": payer["name"],
            "payer_upi_id": payer["upi_id"],
            "recipient_name": transaction[
                "recipient_name"
            ],
            "recipient_upi_id": transaction[
                "recipient_upi_id"
            ],
            "amount": transaction[
                "amount"
            ],
            "risk_score": transaction[
                "risk_score"
            ],
            "signals": signals,
            "available_balance": payer[
                "balance"
            ],
            "new_balance": payer[
                "balance"
            ],
            "balance_deducted": False,
            "model_used": (
                "RandomForestRegressor"
                if MODEL is not None
                else "WeightedFallback"
            ),
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Authentication verification failed: {exc}",
        )

    finally:
        conn.close()


# ============================================================
# RESET DASHBOARD
# ============================================================

@app.post("/reset-dashboard")
def reset_dashboard() -> Dict[str, Any]:

    conn = get_conn()

    try:
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

        # Restore the exact demo balances.
        for payer in DEFAULT_PAYEES:
            conn.execute(
                """
                UPDATE payees
                SET
                    name=?,
                    balance=?,
                    upi_id=?
                WHERE user_id=?
                """,
                (
                    payer["name"],
                    payer["balance"],
                    payer["upi_id"],
                    payer["user_id"],
                ),
            )

        conn.commit()

        return {
            "success": True,
            "message": (
                "Dashboard reset successfully. "
                "Transaction history, challenges, "
                "device history and location history "
                "were cleared."
            ),
            "balances": {
                payer["name"]: payer["balance"]
                for payer in DEFAULT_PAYEES
            },
            "balance_deducted": False,
        }

    except Exception as exc:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Dashboard reset failed: {exc}",
        )

    finally:
        conn.close()


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "SecureFlow AI Risk Engine",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "users": "GET /users",
            "user": "GET /users/{payer_id}",
            "transactions": "GET /transactions/{payer_id}",
            "questions": "GET /questions/{payer_id}",
            "analyze": "POST /analyze-payment",
            "verify": "POST /verify-challenge",
            "reset": "POST /reset-dashboard",
        },
        "risk_bands": {
            "0-49": "ALLOW",
            "50-79": "DYNAMIC AUTHENTICATION",
            "80-100": "INSECURE / BLOCK",
        },
        "visible_risk_switches": 8,
        "amount_switch": False,
        "balance_deduction": False,
    }


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
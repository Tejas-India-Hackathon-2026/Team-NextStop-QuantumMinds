from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
import math
import re

# ============================================================
# SECUREFLOW-AI
# DATABASE-DRIVEN BEHAVIOURAL FRAUD ENGINE
# ============================================================

app = FastAPI(title="SecureFlow-AI Behaviour Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# DATABASE LOCATION
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

POSSIBLE_DATABASES = [
    "SecureFlow-AI.db",
    "secureflow-ai.db",
    "secureflow.db",
    "secureflow_ai.db",
    "database.db",
    "transactions.db",
]

DB_PATH = None

for filename in POSSIBLE_DATABASES:
    candidate = BASE_DIR / filename
    if candidate.exists():
        DB_PATH = candidate
        break

if DB_PATH is None:
    db_files = list(BASE_DIR.glob("*.db"))
    if db_files:
        DB_PATH = db_files[0]

if DB_PATH is None:
    DB_PATH = BASE_DIR / "SecureFlow-AI.db"


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_connection():
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def get_tables(connection):
    rows = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()

    return [row["name"] for row in rows]


def get_columns(connection, table):
    rows = connection.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    return [row["name"] for row in rows]


def normalize(value):
    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        str(value).lower()
    )


def find_table(connection, keywords):
    tables = get_tables(connection)

    best_table = None
    best_score = 0

    for table in tables:

        name = normalize(table)
        score = 0

        for keyword in keywords:
            if normalize(keyword) in name:
                score += 1

        columns = get_columns(connection, table)

        for column in columns:
            column_name = normalize(column)

            for keyword in keywords:
                if normalize(keyword) in column_name:
                    score += 0.5

        if score > best_score:
            best_score = score
            best_table = table

    return best_table


def find_column(columns, aliases):

    normalized_columns = {
        normalize(column): column
        for column in columns
    }

    # Exact match first
    for alias in aliases:
        key = normalize(alias)

        if key in normalized_columns:
            return normalized_columns[key]

    # Partial match
    for column in columns:

        normalized = normalize(column)

        for alias in aliases:

            alias_normalized = normalize(alias)

            if (
                alias_normalized in normalized
                or normalized in alias_normalized
            ):
                return column

    return None


def safe_float(value, default=0.0):

    try:
        return float(value)
    except:
        return default


def safe_int(value, default=0):

    try:
        return int(value)
    except:
        return default


def parse_datetime(value):

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
    ]

    for fmt in formats:

        try:
            return datetime.strptime(text, fmt)
        except:
            pass

    return None


def row_value(row, columns, aliases, default=None):

    column = find_column(columns, aliases)

    if column is None:
        return default

    return row[column]


# ============================================================
# DATABASE DISCOVERY
# ============================================================

def discover_schema(connection):

    users_table = find_table(
        connection,
        [
            "users",
            "user",
            "profiles",
            "customers",
            "accounts"
        ]
    )

    beneficiaries_table = find_table(
        connection,
        [
            "beneficiaries",
            "beneficiary",
            "recipients",
            "recipient",
            "contacts"
        ]
    )

    transactions_table = find_table(
        connection,
        [
            "transactions",
            "transaction",
            "payments",
            "payment",
            "history"
        ]
    )

    return {
        "users": users_table,
        "beneficiaries": beneficiaries_table,
        "transactions": transactions_table,
    }


# ============================================================
# API MODELS
# ============================================================

class PaymentRequest(BaseModel):

    amount: float
    recipient_id: str

    # Automatically supplied by browser.
    # These are NOT manually controlled risk switches.
    device_id: str = ""
    timezone: str = ""

    latitude: float | None = None
    longitude: float | None = None


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "message": "SecureFlow-AI Behaviour Engine",
        "database": str(DB_PATH.name),
        "status": "running"
    }


# ============================================================
# DATABASE STATUS
# ============================================================

@app.get("/database-status")
def database_status():

    connection = get_connection()

    try:

        tables = get_tables(connection)

        schema = discover_schema(connection)

        return {
            "database": DB_PATH.name,
            "connected": True,
            "tables": tables,
            "detected_schema": schema
        }

    finally:

        connection.close()


# ============================================================
# GET PAYER FROM DATABASE
# ============================================================

@app.get("/profile")
def profile():

    connection = get_connection()

    try:

        schema = discover_schema(connection)

        users_table = schema["users"]

        if not users_table:

            raise HTTPException(
                status_code=500,
                detail="Users table was not found in SQLite database."
            )

        columns = get_columns(
            connection,
            users_table
        )

        rows = connection.execute(
            f'SELECT * FROM "{users_table}" LIMIT 1'
        ).fetchall()

        if not rows:

            raise HTTPException(
                status_code=404,
                detail="No users found in database."
            )

        row = rows[0]

        user_id = row_value(
            row,
            columns,
            [
                "user_id",
                "userid",
                "id",
                "customer_id"
            ],
            "1"
        )

        name = row_value(
            row,
            columns,
            [
                "name",
                "user_name",
                "username",
                "full_name",
                "customer_name"
            ],
            "User"
        )

        return {
            "user_id": str(user_id),
            "name": str(name)
        }

    finally:

        connection.close()


# ============================================================
# GET RECIPIENTS FROM DATABASE
# ============================================================

@app.get("/recipients")
def recipients():

    connection = get_connection()

    try:

        schema = discover_schema(connection)

        table = schema["beneficiaries"]

        if not table:

            raise HTTPException(
                status_code=500,
                detail="Beneficiary/recipient table was not found."
            )

        columns = get_columns(
            connection,
            table
        )

        rows = connection.execute(
            f'SELECT * FROM "{table}"'
        ).fetchall()

        result = []

        for row in rows:

            recipient_id = row_value(
                row,
                columns,
                [
                    "beneficiary_id",
                    "beneficiaryid",
                    "recipient_id",
                    "recipientid",
                    "contact_id",
                    "id",
                    "upi_id"
                ]
            )

            name = row_value(
                row,
                columns,
                [
                    "beneficiary_name",
                    "recipient_name",
                    "name",
                    "full_name",
                    "beneficiary",
                    "recipient"
                ]
            )

            upi_id = row_value(
                row,
                columns,
                [
                    "upi_id",
                    "upi",
                    "vpa",
                    "upi_address"
                ],
                ""
            )

            if name is None:
                continue

            result.append({
                "id": str(
                    recipient_id
                    if recipient_id is not None
                    else upi_id
                    if upi_id
                    else name
                ),
                "name": str(name),
                "upi_id": str(upi_id or "")
            })

        return result

    finally:

        connection.close()


# ============================================================
# BEHAVIOURAL ENGINE
# ============================================================

def calculate_risk(
    connection,
    user_id,
    recipient_id,
    amount,
    device_id,
    timezone,
    latitude,
    longitude
):

    schema = discover_schema(connection)

    users_table = schema["users"]
    beneficiaries_table = schema["beneficiaries"]
    transactions_table = schema["transactions"]

    risk = 0
    reasons = []
    signals = []

    # --------------------------------------------------------
    # SCORE DEFINITIONS
    # --------------------------------------------------------

    # Your exact scoring system:
    #
    # Amount deviation          +10
    # Time anomaly               +7
    # Frequency anomaly         +12
    # New device                +15
    # Unusual location          +15
    # Sudden location change     +6
    # Unknown beneficiary       +12
    # Previous transaction      +13
    # Typical amount            +10
    #
    # TOTAL                     100
    # --------------------------------------------------------

    # --------------------------------------------------------
    # USER INFORMATION
    # --------------------------------------------------------

    user_row = None

    if users_table:

        user_columns = get_columns(
            connection,
            users_table
        )

        id_column = find_column(
            user_columns,
            [
                "user_id",
                "userid",
                "id",
                "customer_id"
            ]
        )

        if id_column:

            user_row = connection.execute(
                f'''
                SELECT *
                FROM "{users_table}"
                WHERE "{id_column}" = ?
                LIMIT 1
                ''',
                (user_id,)
            ).fetchone()

    # --------------------------------------------------------
    # HISTORICAL TRANSACTIONS
    # --------------------------------------------------------

    transaction_rows = []

    if transactions_table:

        transaction_columns = get_columns(
            connection,
            transactions_table
        )

        user_column = find_column(
            transaction_columns,
            [
                "user_id",
                "userid",
                "customer_id",
                "payer_id"
            ]
        )

        if user_column:

            transaction_rows = connection.execute(
                f'''
                SELECT *
                FROM "{transactions_table}"
                WHERE "{user_column}" = ?
                ''',
                (user_id,)
            ).fetchall()

        else:

            transaction_rows = connection.execute(
                f'''
                SELECT *
                FROM "{transactions_table}"
                '''
            ).fetchall()

    else:

        transaction_columns = []

    # --------------------------------------------------------
    # AMOUNT BEHAVIOUR
    # --------------------------------------------------------

    historical_amounts = []

    amount_column = find_column(
        transaction_columns,
        [
            "amount",
            "transaction_amount",
            "payment_amount",
            "value"
        ]
    )

    if amount_column:

        for row in transaction_rows:

            value = safe_float(
                row[amount_column]
            )

            if value > 0:
                historical_amounts.append(value)

    average_amount = 0

    if historical_amounts:

        average_amount = (
            sum(historical_amounts)
            / len(historical_amounts)
        )

    elif user_row and users_table:

        user_columns = get_columns(
            connection,
            users_table
        )

        average_column = find_column(
            user_columns,
            [
                "average_transaction",
                "average_amount",
                "avg_amount",
                "typical_amount"
            ]
        )

        if average_column:

            average_amount = safe_float(
                user_row[average_column]
            )

    amount_anomaly = False

    if average_amount > 0:

        # Significant deviation from historical behaviour.
        if amount > average_amount * 2:

            amount_anomaly = True

    elif amount > 10000:

        amount_anomaly = True

    if amount_anomaly:

        risk += 10

        reasons.append(
            "Amount deviates significantly from normal behaviour"
        )

        signals.append({
            "name": "Amount deviation",
            "score": 10
        })

    # --------------------------------------------------------
    # TIME BEHAVIOUR
    # --------------------------------------------------------

    now = datetime.now()

    current_hour = now.hour

    time_anomaly = False

    if user_row and users_table:

        user_columns = get_columns(
            connection,
            users_table
        )

        start_column = find_column(
            user_columns,
            [
                "normal_start_time",
                "usual_start_time",
                "usual_start",
                "start_time"
            ]
        )

        end_column = find_column(
            user_columns,
            [
                "normal_end_time",
                "usual_end_time",
                "usual_end",
                "end_time"
            ]
        )

        if start_column and end_column:

            try:

                start = int(
                    str(
                        user_row[start_column]
                    )[:2]
                )

                end = int(
                    str(
                        user_row[end_column]
                    )[:2]
                )

                if start <= end:

                    if not (
                        start <= current_hour <= end
                    ):
                        time_anomaly = True

                else:

                    if not (
                        current_hour >= start
                        or current_hour <= end
                    ):
                        time_anomaly = True

            except:

                pass

    if time_anomaly:

        risk += 7

        reasons.append(
            "Transaction time is unusual for this user"
        )

        signals.append({
            "name": "Time anomaly",
            "score": 7
        })

    # --------------------------------------------------------
    # TRANSACTION FREQUENCY
    # --------------------------------------------------------

    recent_transactions = []

    date_column = find_column(
        transaction_columns,
        [
            "transaction_time",
            "transaction_date",
            "created_at",
            "timestamp",
            "date",
            "time"
        ]
    )

    if date_column:

        for row in transaction_rows:

            dt = parse_datetime(
                row[date_column]
            )

            if dt:

                if now - dt <= timedelta(days=1):

                    recent_transactions.append(dt)

    frequency_anomaly = False

    normal_daily = None

    if user_row and users_table:

        user_columns = get_columns(
            connection,
            users_table
        )

        frequency_column = find_column(
            user_columns,
            [
                "typical_daily_transactions",
                "daily_transactions",
                "average_daily_transactions",
                "usual_frequency"
            ]
        )

        if frequency_column:

            normal_daily = safe_int(
                user_row[frequency_column]
            )

    if normal_daily and normal_daily > 0:

        if len(recent_transactions) >= normal_daily * 2:

            frequency_anomaly = True

    else:

        if len(recent_transactions) >= 6:

            frequency_anomaly = True

    if frequency_anomaly:

        risk += 12

        reasons.append(
            "Transaction frequency is higher than normal"
        )

        signals.append({
            "name": "Frequency anomaly",
            "score": 12
        })

    # --------------------------------------------------------
    # DEVICE BEHAVIOUR
    # --------------------------------------------------------

    known_device = False

    if user_row and users_table and device_id:

        user_columns = get_columns(
            connection,
            users_table
        )

        device_column = find_column(
            user_columns,
            [
                "known_device",
                "trusted_device",
                "device_id",
                "device"
            ]
        )

        if device_column:

            stored_device = str(
                user_row[device_column]
            ).strip()

            known_device = (
                stored_device.lower()
                == device_id.lower()
            )

    if not known_device:

        risk += 15

        reasons.append(
            "New or unknown device/session"
        )

        signals.append({
            "name": "New device",
            "score": 15
        })

    # --------------------------------------------------------
    # LOCATION BEHAVIOUR
    # --------------------------------------------------------

    unusual_location = False
    sudden_location_change = False

    stored_latitude = None
    stored_longitude = None

    if user_row and users_table:

        user_columns = get_columns(
            connection,
            users_table
        )

        lat_column = find_column(
            user_columns,
            [
                "latitude",
                "usual_latitude",
                "location_latitude"
            ]
        )

        lon_column = find_column(
            user_columns,
            [
                "longitude",
                "usual_longitude",
                "location_longitude"
            ]
        )

        if lat_column:

            stored_latitude = safe_float(
                user_row[lat_column],
                None
            )

        if lon_column:

            stored_longitude = safe_float(
                user_row[lon_column],
                None
            )

    # If the database contains coordinates,
    # calculate real geographic distance.

    if (
        latitude is not None
        and longitude is not None
        and stored_latitude is not None
        and stored_longitude is not None
    ):

        R = 6371

        lat1 = math.radians(
            stored_latitude
        )

        lat2 = math.radians(
            latitude
        )

        dlat = math.radians(
            latitude - stored_latitude
        )

        dlon = math.radians(
            longitude - stored_longitude
        )

        a = (
            math.sin(dlat / 2) ** 2
            +
            math.cos(lat1)
            *
            math.cos(lat2)
            *
            math.sin(dlon / 2) ** 2
        )

        distance = (
            2
            * R
            * math.asin(
                math.sqrt(a)
            )
        )

        if distance > 25:

            unusual_location = True

        if distance > 100:

            sudden_location_change = True

    if unusual_location:

        risk += 15

        reasons.append(
            "Current location differs from usual location"
        )

        signals.append({
            "name": "Unusual location",
            "score": 15
        })

    if sudden_location_change:

        risk += 6

        reasons.append(
            "Sudden location change detected"
        )

        signals.append({
            "name": "Sudden location change",
            "score": 6
        })

    # --------------------------------------------------------
    # BENEFICIARY BEHAVIOUR
    # --------------------------------------------------------

    beneficiary_row = None

    if beneficiaries_table:

        beneficiary_columns = get_columns(
            connection,
            beneficiaries_table
        )

        id_column = find_column(
            beneficiary_columns,
            [
                "beneficiary_id",
                "beneficiaryid",
                "recipient_id",
                "recipientid",
                "id",
                "upi_id"
            ]
        )

        if id_column:

            beneficiary_row = connection.execute(
                f'''
                SELECT *
                FROM "{beneficiaries_table}"
                WHERE "{id_column}" = ?
                LIMIT 1
                ''',
                (recipient_id,)
            ).fetchone()

        if beneficiary_row is None:

            name_column = find_column(
                beneficiary_columns,
                [
                    "beneficiary_name",
                    "recipient_name",
                    "name",
                    "full_name"
                ]
            )

            upi_column = find_column(
                beneficiary_columns,
                [
                    "upi_id",
                    "upi",
                    "vpa"
                ]
            )

            if name_column:

                beneficiary_row = connection.execute(
                    f'''
                    SELECT *
                    FROM "{beneficiaries_table}"
                    WHERE "{name_column}" = ?
                    LIMIT 1
                    ''',
                    (recipient_id,)
                ).fetchone()

            elif upi_column:

                beneficiary_row = connection.execute(
                    f'''
                    SELECT *
                    FROM "{beneficiaries_table}"
                    WHERE "{upi_column}" = ?
                    LIMIT 1
                    ''',
                    (recipient_id,)
                ).fetchone()

    known_beneficiary = beneficiary_row is not None

    if not known_beneficiary:

        risk += 12

        reasons.append(
            "Recipient is not present in the user's known beneficiary history"
        )

        signals.append({
            "name": "Unknown beneficiary",
            "score": 12
        })

    # --------------------------------------------------------
    # PREVIOUS TRANSACTIONS WITH RECIPIENT
    # --------------------------------------------------------

    previous_transaction = False
    beneficiary_historical_amounts = []

    if transactions_table and transaction_rows:

        recipient_column = find_column(
            transaction_columns,
            [
                "beneficiary_id",
                "recipient_id",
                "beneficiary",
                "recipient",
                "upi_id",
                "receiver_upi",
                "to_upi"
            ]
        )

        if recipient_column:

            for row in transaction_rows:

                value = str(
                    row[recipient_column]
                ).strip().lower()

                if value == str(
                    recipient_id
                ).strip().lower():

                    previous_transaction = True

                    if amount_column:

                        historical_value = safe_float(
                            row[amount_column]
                        )

                        if historical_value > 0:

                            beneficiary_historical_amounts.append(
                                historical_value
                            )

    if not previous_transaction:

        risk += 13

        reasons.append(
            "No previous transaction history with this recipient"
        )

        signals.append({
            "name": "Previous transaction history",
            "score": 13
        })

    # --------------------------------------------------------
    # TYPICAL AMOUNT WITH THIS BENEFICIARY
    # --------------------------------------------------------

    typical_amount = True

    if beneficiary_historical_amounts:

        beneficiary_average = (
            sum(
                beneficiary_historical_amounts
            )
            /
            len(
                beneficiary_historical_amounts
            )
        )

        if amount > beneficiary_average * 2:

            typical_amount = False

    elif beneficiary_row and beneficiaries_table:

        beneficiary_columns = get_columns(
            connection,
            beneficiaries_table
        )

        avg_column = find_column(
            beneficiary_columns,
            [
                "average_amount",
                "avg_amount",
                "typical_amount"
            ]
        )

        if avg_column:

            beneficiary_average = safe_float(
                beneficiary_row[avg_column]
            )

            if (
                beneficiary_average > 0
                and amount > beneficiary_average * 2
            ):

                typical_amount = False

    if not typical_amount:

        risk += 10

        reasons.append(
            "Amount is unusual for this recipient"
        )

        signals.append({
            "name": "Unusual beneficiary amount",
            "score": 10
        })

    # --------------------------------------------------------
    # HARD CAP
    # --------------------------------------------------------

    risk = min(
        max(risk, 0),
        100
    )

    # --------------------------------------------------------
    # DECISION
    # --------------------------------------------------------

    if risk <= 40:

        decision = "ALLOW"
        status = "Payment approved"

    elif risk <= 70:

        decision = "ALERT"
        status = "Payment temporarily held"

    else:

        decision = "BLOCK"
        status = "Payment blocked"

    # --------------------------------------------------------
    # DYNAMIC QUESTIONS
    #
    # ONLY GENERATED WHEN RISK > 50
    # --------------------------------------------------------

    dynamic_questions = []

    if risk > 50:

        if amount_anomaly:

            dynamic_questions.append(
                f"Can you confirm this payment of ₹{amount:,.2f}?"
            )

        if time_anomaly:

            dynamic_questions.append(
                "This payment is being made at an unusual time. Did you initiate it?"
            )

        if frequency_anomaly:

            dynamic_questions.append(
                "We detected unusually frequent payment activity. Are these transactions yours?"
            )

        if not known_device:

            dynamic_questions.append(
                "This payment is being made from a new device. Do you recognize this device?"
            )

        if unusual_location:

            dynamic_questions.append(
                "The current location differs from your usual payment location. Did you initiate this payment?"
            )

        if sudden_location_change:

            dynamic_questions.append(
                "A significant location change was detected. Did you recently travel?"
            )

        if not known_beneficiary:

            dynamic_questions.append(
                "This recipient is not part of your previous payment history. Do you recognize this recipient?"
            )

        if not previous_transaction:

            dynamic_questions.append(
                "You have no previous payment history with this recipient. Did you intend to pay them?"
            )

        if not typical_amount:

            dynamic_questions.append(
                "The amount is significantly different from your usual payments to this recipient. Is this amount correct?"
            )

    return {
        "risk_score": risk,
        "decision": decision,
        "status": status,
        "signals": signals,
        "reasons": reasons,
        "dynamic_questions": dynamic_questions
    }


# ============================================================
# PAYMENT ANALYSIS ENDPOINT
# ============================================================

@app.post("/transaction")
def transaction(payment: PaymentRequest):

    if payment.amount <= 0:

        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero."
        )

    connection = get_connection()

    try:

        # The first user in the database is the
        # payer for this demonstration.

        schema = discover_schema(connection)

        users_table = schema["users"]

        if not users_table:

            raise HTTPException(
                status_code=500,
                detail="Users table not found."
            )

        user_columns = get_columns(
            connection,
            users_table
        )

        user_id_column = find_column(
            user_columns,
            [
                "user_id",
                "userid",
                "id",
                "customer_id"
            ]
        )

        if not user_id_column:

            raise HTTPException(
                status_code=500,
                detail="Could not identify user ID column."
            )

        user_row = connection.execute(
            f'''
            SELECT *
            FROM "{users_table}"
            ORDER BY "{user_id_column}"
            LIMIT 1
            '''
        ).fetchone()

        if not user_row:

            raise HTTPException(
                status_code=404,
                detail="No payer found in database."
            )

        user_id = user_row[user_id_column]

        result = calculate_risk(
            connection=connection,
            user_id=user_id,
            recipient_id=payment.recipient_id,
            amount=payment.amount,
            device_id=payment.device_id,
            timezone=payment.timezone,
            latitude=payment.latitude,
            longitude=payment.longitude
        )

        return result

    finally:

        connection.close()


# ============================================================
# RUN:
#
# uvicorn main:app --reload
# ============================================================
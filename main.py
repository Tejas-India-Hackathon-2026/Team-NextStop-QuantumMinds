from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI(title="SecureFlow-AI Behaviour Engine")

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# TRANSACTION MODEL
# ---------------------------------------------------------

class Transaction(BaseModel):

    # Transaction behaviour
    amount: float
    unusual_time: bool
    unusual_frequency: bool
    high_velocity: bool

    # Device behaviour
    known_device: bool
    device_changed: bool

    # Location behaviour
    usual_location: bool
    sudden_location_change: bool

    # Relationship / history
    known_beneficiary: bool
    previous_transactions: bool
    typical_amount_with_beneficiary: bool
    beneficiary_matches_history: bool


# ---------------------------------------------------------
# ANSWER MODEL
# ---------------------------------------------------------

class SecurityAnswers(BaseModel):

    answers: List[str]


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "SecureFlow-AI Behavioural Fraud Detection Engine",
        "status": "running"
    }


# ---------------------------------------------------------
# DYNAMIC QUESTION GENERATOR
# ---------------------------------------------------------

def generate_dynamic_questions(tx: Transaction, reasons):

    questions = []

    # The questions are generated according to
    # the suspicious behavioural signals detected.

    if "Amount pattern anomaly" in reasons:

        questions.append(
            f"Can you confirm that you intentionally initiated "
            f"this payment of ₹{tx.amount:,.2f}?"
        )

    if "Unusual transaction time" in reasons:

        questions.append(
            "This payment is being made at an unusual time "
            "compared with your normal activity. Did you initiate it?"
        )

    if "Unusual transaction frequency" in reasons:

        questions.append(
            "Your recent transaction activity is higher than "
            "your normal pattern. Are these transactions authorized by you?"
        )

    if "High transaction velocity" in reasons:

        questions.append(
            "Several transactions have occurred within a short period. "
            "Did you personally initiate this activity?"
        )

    if "New device/session" in reasons:

        questions.append(
            "This transaction is coming from a device or session "
            "that differs from your usual device. Did you recently "
            "change or log in from another device?"
        )

    if "Location anomaly" in reasons:

        questions.append(
            "This payment is being made from a location that differs "
            "from your usual transaction location. Are you currently there?"
        )

    if "Sudden location change" in reasons:

        questions.append(
            "Your recent transaction location changed unusually quickly. "
            "Have you recently travelled or changed location?"
        )

    if "Unknown beneficiary" in reasons:

        questions.append(
            "This recipient does not match your usual payment relationships. "
            "Do you recognize and trust this beneficiary?"
        )

    if "No previous transaction history" in reasons:

        questions.append(
            "You have no previous transaction history with this recipient. "
            "Have you intentionally chosen this beneficiary?"
        )

    if "Unusual beneficiary amount" in reasons:

        questions.append(
            "The amount being sent to this beneficiary differs from "
            "your normal payment pattern. Is this amount intentional?"
        )

    if "Behaviour deviation" in reasons:

        questions.append(
            "Several independent signals differ from your normal "
            "behavioural footprint. Can you confirm that you initiated "
            "this transaction yourself?"
        )

    # Make sure the system always has something to ask
    # when an ALERT is triggered.

    if not questions:

        questions.append(
            "Please confirm that you personally initiated this transaction."
        )

    return questions


# ---------------------------------------------------------
# RISK ENGINE
# ---------------------------------------------------------

@app.post("/transaction")
def transaction(tx: Transaction):

    risk = 0
    reasons = []

    # -----------------------------------------------------
    # A. TRANSACTION BEHAVIOUR
    # -----------------------------------------------------

    # Amount = 10
    if tx.amount > 10000:

        risk += 10

        reasons.append(
            "Amount pattern anomaly"
        )

    # Time = 7
    if tx.unusual_time:

        risk += 7

        reasons.append(
            "Unusual transaction time"
        )

    # Frequency = 12
    if tx.unusual_frequency:

        risk += 12

        reasons.append(
            "Unusual transaction frequency"
        )

    # Velocity = included within transaction behaviour
    # and limited so that maximum risk remains 100.

    if tx.high_velocity:

        risk += 10

        reasons.append(
            "High transaction velocity"
        )

    # -----------------------------------------------------
    # B. DEVICE BEHAVIOUR
    # -----------------------------------------------------

    # New device = 15

    if not tx.known_device:

        risk += 15

        reasons.append(
            "New device/session"
        )

    # Device/session changed

    if tx.device_changed:

        risk += 5

        reasons.append(
            "Device/session changed"
        )

    # -----------------------------------------------------
    # C. LOCATION BEHAVIOUR
    # -----------------------------------------------------

    # Unusual location = 15

    if not tx.usual_location:

        risk += 15

        reasons.append(
            "Location anomaly"
        )

    # Sudden location change = 6

    if tx.sudden_location_change:

        risk += 6

        reasons.append(
            "Sudden location change"
        )

    # -----------------------------------------------------
    # D. RELATIONSHIP / HISTORY
    # -----------------------------------------------------

    # Unknown beneficiary = 12

    if not tx.known_beneficiary:

        risk += 12

        reasons.append(
            "Unknown beneficiary"
        )

    # No previous transaction = 13

    if not tx.previous_transactions:

        risk += 13

        reasons.append(
            "No previous transaction history"
        )

    # Unusual amount with beneficiary = 10

    if not tx.typical_amount_with_beneficiary:

        risk += 10

        reasons.append(
            "Unusual beneficiary amount"
        )

    # Behaviour mismatch = 15

    if not tx.beneficiary_matches_history:

        risk += 15

        reasons.append(
            "Behaviour deviation"
        )

    # -----------------------------------------------------
    # CAP SCORE AT 100
    # -----------------------------------------------------

    risk = min(risk, 100)

    # -----------------------------------------------------
    # RISK CLASSIFICATION
    # -----------------------------------------------------

    if risk <= 40:

        risk_level = "LOW"
        decision = "ALLOW"
        transaction_delayed = False

    elif risk <= 70:

        risk_level = "MEDIUM"
        decision = "ALERT"
        transaction_delayed = True

    else:

        risk_level = "HIGH"
        decision = "BLOCK"
        transaction_delayed = True

    # -----------------------------------------------------
    # DYNAMIC AI QUESTIONS
    # -----------------------------------------------------

    ai_questions = []

    if decision == "ALERT":

        ai_questions = generate_dynamic_questions(
            tx,
            reasons
        )

    elif decision == "BLOCK":

        ai_questions = [
            "This transaction has been blocked because multiple "
            "independent behavioural signals indicate a high-risk pattern."
        ]

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "risk_score": risk,

        "risk_level": risk_level,

        "decision": decision,

        "transaction_delayed": transaction_delayed,

        "authentication_required":
            decision == "ALERT",

        "independent_signals": len(reasons),

        "reasons": reasons,

        "ai_questions": ai_questions
    }


# ---------------------------------------------------------
# SECURITY ANSWER EVALUATION
# ---------------------------------------------------------

@app.post("/transaction/verify")
def verify_transaction(data: SecurityAnswers):

    answers = [
        answer.strip().lower()
        for answer in data.answers
    ]

    positive_words = [
        "yes",
        "yeah",
        "y",
        "correct",
        "true",
        "myself",
        "mine",
        "authorized",
        "intentional",
        "travelled",
        "travel",
        "changed"
    ]

    negative_words = [
        "no",
        "not",
        "never",
        "unknown",
        "fake",
        "fraud",
        "stolen",
        "unauthorized"
    ]

    positive_score = 0
    negative_score = 0

    for answer in answers:

        for word in positive_words:

            if word in answer:
                positive_score += 1

        for word in negative_words:

            if word in answer:
                negative_score += 1

    # -----------------------------------------------------
    # FINAL AUTHENTICATION DECISION
    # -----------------------------------------------------

    if negative_score > positive_score:

        final_decision = "BLOCK"

        message = (
            "Verification failed. The transaction has been blocked."
        )

    elif positive_score > 0:

        final_decision = "ALLOW"

        message = (
            "Verification completed. The transaction can proceed."
        )

    else:

        final_decision = "REVIEW"

        message = (
            "The answers were inconclusive. Additional verification "
            "is required."
        )

    return {

        "final_decision": final_decision,

        "message": message,

        "positive_signals": positive_score,

        "negative_signals": negative_score
    }
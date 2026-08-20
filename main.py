# database/mongodb.py

from pymongo import MongoClient

client = MongoClient(
    "mongodb://localhost:27017"
)

db = client["secureflow"]

transactions = db["transactions"]


def save_transaction(transaction, result):

    document = {
        "transaction_id": transaction.transaction_id,
        "user_id": transaction.user_id,
        "amount": transaction.amount,
        "merchant_id": transaction.merchant_id,
        "device_id": transaction.device_id,
        "location": transaction.location,

        "risk_score": result["risk_score"],
        "fraud_probability": result["fraud_probability"],
        "action": result["action"],

        "created_at": __import__("datetime")
            .datetime.utcnow()
    }

    transactions.insert_one(document)

    return document
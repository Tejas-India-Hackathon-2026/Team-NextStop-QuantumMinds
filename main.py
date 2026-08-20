from risk_engine import calculate_risk


transaction = {

    "amount": 85000,

    "hour": 2,

    "sender_txn_count_24h": 25,

    "receiver_txn_count_24h": 1,

    "new_recipient": 1,

    "previous_connection": 0,

    "device_match": 0,

    "location_change_km": 850,

    "name_match": 0,

    "beneficiary_age_days": 1,

    "amount_deviation": 4.8,

    "failed_attempts": 3,

    "velocity": 20
}


result = calculate_risk(transaction)


print("\n========== SECUREFLOW AI ==========")

print("Fraud Probability:",
      result["fraud_probability"])

print("Risk Score:",
      result["risk_score"])

print("Decision:",
      result["decision"])

print("===================================")
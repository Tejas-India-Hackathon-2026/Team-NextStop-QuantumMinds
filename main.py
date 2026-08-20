import joblib
import pandas as pd


# Load trained model
model = joblib.load("secureflow_fraud_model.pkl")
features = joblib.load("model_features.pkl")


def calculate_risk(transaction):

    # Convert transaction into dataframe
    data = pd.DataFrame([transaction])

    # Select required features
    X = data[features]

    # Fraud probability
    fraud_probability = model.predict_proba(X)[0][1]

    # Convert probability to 0-100
    risk_score = round(fraud_probability * 100, 2)

    # Decision
    if risk_score <= 30:

        decision = "ALLOW"

    elif risk_score <= 70:

        decision = "ALERT"

    else:

        decision = "BLOCK"

    return {
        "fraud_probability": round(fraud_probability, 4),
        "risk_score": risk_score,
        "decision": decision
    }
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report
)

from xgboost import XGBClassifier


# ==========================================
# 1. LOAD DATASET
# ==========================================

df = pd.read_csv("upi_transactions.csv")

print("Dataset loaded")
print("Rows:", len(df))


# ==========================================
# 2. FEATURES
# ==========================================

features = [
    "amount",
    "hour",
    "sender_txn_count_24h",
    "receiver_txn_count_24h",
    "new_recipient",
    "previous_connection",
    "device_match",
    "location_change_km",
    "name_match",
    "beneficiary_age_days",
    "amount_deviation",
    "failed_attempts",
    "velocity"
]

X = df[features]
y = df["fraud"]


# ==========================================
# 3. TRAIN / TEST SPLIT
# ==========================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# ==========================================
# 4. XGBOOST MODEL
# ==========================================

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    random_state=42
)


# ==========================================
# 5. TRAIN
# ==========================================

print("Training model...")

model.fit(
    X_train,
    y_train
)

print("Training completed")


# ==========================================
# 6. PREDICTION
# ==========================================

y_pred = model.predict(X_test)

y_probability = model.predict_proba(X_test)[:, 1]


# ==========================================
# 7. MODEL PERFORMANCE
# ==========================================

accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_probability)

print("\n========== MODEL PERFORMANCE ==========")

print("Accuracy :", round(accuracy * 100, 2), "%")
print("Precision:", round(precision * 100, 2), "%")
print("Recall   :", round(recall * 100, 2), "%")
print("F1 Score :", round(f1 * 100, 2), "%")
print("ROC-AUC  :", round(auc * 100, 2), "%")

print("\nClassification Report")
print(classification_report(y_test, y_pred))


# ==========================================
# 8. SAVE MODEL
# ==========================================

joblib.dump(model, "secureflow_fraud_model.pkl")

joblib.dump(features, "model_features.pkl")

print("\nModel saved successfully!")
print("secureflow_fraud_model.pkl")
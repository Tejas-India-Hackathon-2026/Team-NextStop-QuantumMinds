# ml/train.py

import pandas as pd

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib


def train_fraud_model(csv_file):

    data = pd.read_csv(csv_file)

    X = data.drop(
        columns=["is_fraud"]
    )

    y = data["is_fraud"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    joblib.dump(
        model,
        "models/xgboost_fraud_model.pkl"
    )

    return {
        "accuracy": round(accuracy, 4),
        "model_saved": True
    }
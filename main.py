# services/fraud_cases.py

import uuid
from datetime import datetime


class FraudCaseManager:

    def __init__(self):

        self.cases = {}

    def create_case(
        self,
        transaction_id,
        user_id,
        risk_score,
        reasons
    ):

        case_id = (
            "CASE-"
            + uuid.uuid4().hex[:10].upper()
        )

        case = {
            "case_id": case_id,
            "transaction_id": transaction_id,
            "user_id": user_id,
            "risk_score": risk_score,
            "reasons": reasons,
            "status": "OPEN",
            "created_at":
                datetime.utcnow().isoformat()
        }

        self.cases[case_id] = case

        return case

    def update_status(
        self,
        case_id,
        status
    ):

        if case_id not in self.cases:

            raise ValueError(
                "Fraud case not found."
            )

        self.cases[case_id]["status"] = status

        return self.cases[case_id]

    def get_case(self, case_id):

        return self.cases.get(case_id)
# services/beneficiary_risk.py

from datetime import datetime


class BeneficiaryRiskAnalyzer:

    def analyze(
        self,
        beneficiary_id,
        known_beneficiaries,
        beneficiary_age_days
    ):

        risk = 0
        reasons = []

        if beneficiary_id not in known_beneficiaries:
            risk += 35
            reasons.append(
                "Beneficiary has not been used previously."
            )

        if beneficiary_age_days < 1:
            risk += 30
            reasons.append(
                "Beneficiary was recently added."
            )

        elif beneficiary_age_days < 7:
            risk += 15
            reasons.append(
                "Beneficiary is relatively new."
            )

        return {
            "risk_score": min(risk, 100),
            "reasons": reasons
        }
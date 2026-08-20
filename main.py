# services/time_risk.py

class TransactionTimeAnalyzer:

    def analyze(
        self,
        transaction_hour,
        normal_hours
    ):

        if transaction_hour in normal_hours:

            return {
                "risk": 0,
                "status": "NORMAL",
                "reason": "Transaction occurred during normal hours."
            }

        if transaction_hour >= 0 and transaction_hour < 5:

            return {
                "risk": 30,
                "status": "HIGH_RISK_TIME",
                "reason": "Transaction occurred during late-night hours."
            }

        return {
            "risk": 15,
            "status": "UNUSUAL_TIME",
            "reason": "Transaction occurred outside normal user activity."
        }
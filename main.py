# services/amount_pattern.py

from collections import Counter


class AmountPatternDetector:

    def analyze(
        self,
        transaction_amounts,
        current_amount
    ):

        if not transaction_amounts:

            return {
                "suspicious": False,
                "reason": "No historical data available."
            }

        counts = Counter(transaction_amounts)

        repeated_amounts = [
            amount
            for amount, count in counts.items()
            if count >= 3
        ]

        if current_amount in repeated_amounts:

            return {
                "suspicious": True,
                "reason":
                    "Repeated transaction amount pattern detected.",
                "amount": current_amount
            }

        return {
            "suspicious": False,
            "reason": "No suspicious amount pattern detected."
        }
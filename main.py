# services/risk_aggregator.py


class RiskAggregator:

    def __init__(self):

        self.weights = {
            "ml": 0.40,
            "rules": 0.20,
            "merchant": 0.15,
            "travel": 0.10,
            "device": 0.15
        }

    def calculate(
        self,
        ml_score,
        rule_score,
        merchant_score,
        travel_score,
        device_score
    ):

        final_score = (

            ml_score *
            self.weights["ml"]

            +

            rule_score *
            self.weights["rules"]

            +

            merchant_score *
            self.weights["merchant"]

            +

            travel_score *
            self.weights["travel"]

            +

            device_score *
            self.weights["device"]
        )

        return round(
            min(final_score, 100),
            2
        )
# services/rule_engine.py


class FraudRule:

    def __init__(
        self,
        name,
        condition,
        weight
    ):

        self.name = name
        self.condition = condition
        self.weight = weight


class RuleEngine:

    def __init__(self):

        self.rules = [

            FraudRule(
                "high_amount",
                lambda x: x["amount"] > 50000,
                20
            ),

            FraudRule(
                "new_device",
                lambda x: x["new_device"],
                15
            ),

            FraudRule(
                "new_location",
                lambda x: x["new_location"],
                10
            ),

            FraudRule(
                "many_failures",
                lambda x: x["failed_attempts"] >= 3,
                15
            ),

            FraudRule(
                "merchant_high_risk",
                lambda x: x["merchant_risk"] >= 70,
                25
            )
        ]

    def evaluate(self, transaction):

        triggered = []
        score = 0

        for rule in self.rules:

            if rule.condition(transaction):

                triggered.append(rule.name)
                score += rule.weight

        return {
            "rule_score": min(score, 100),
            "triggered_rules": triggered
        }
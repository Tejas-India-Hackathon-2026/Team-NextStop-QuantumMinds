# services/bayesian.py

def bayesian_probability(
    fraud_probability,
    feature_probability_given_fraud,
    feature_probability_given_legitimate
):
    """
    Simplified Bayesian update.

    P(Fraud | Feature)
    """

    numerator = (
        feature_probability_given_fraud
        * fraud_probability
    )

    legitimate_probability = 1 - fraud_probability

    denominator = (
        numerator
        +
        feature_probability_given_legitimate
        * legitimate_probability
    )

    if denominator == 0:
        return 0.0

    return numerator / denominator
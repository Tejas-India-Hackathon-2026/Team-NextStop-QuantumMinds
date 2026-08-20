# ml/drift_detector.py

import math


class DriftDetector:

    @staticmethod
    def distribution_difference(
        baseline,
        current
    ):

        if len(baseline) != len(current):
            raise ValueError(
                "Distributions must have "
                "the same number of bins."
            )

        score = 0

        for expected, actual in zip(
            baseline,
            current
        ):

            expected = max(expected, 0.0001)
            actual = max(actual, 0.0001)

            score += (
                (actual - expected)
                * math.log(actual / expected)
            )

        return score

    def detect(
        self,
        baseline,
        current,
        threshold=0.25
    ):

        score = self.distribution_difference(
            baseline,
            current
        )

        return {
            "drift_score": round(score, 4),
            "drift_detected": score >= threshold,
            "recommend_retraining":
                score >= threshold
        }
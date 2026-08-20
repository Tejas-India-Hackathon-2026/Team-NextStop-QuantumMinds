# ml/metrics.py

class FraudMetrics:

    @staticmethod
    def calculate(
        true_values,
        predicted_values
    ):

        if len(true_values) != len(
            predicted_values
        ):

            raise ValueError(
                "Input lengths must match."
            )

        tp = 0
        tn = 0
        fp = 0
        fn = 0

        for actual, predicted in zip(
            true_values,
            predicted_values
        ):

            if actual == 1 and predicted == 1:
                tp += 1

            elif actual == 0 and predicted == 0:
                tn += 1

            elif actual == 0 and predicted == 1:
                fp += 1

            elif actual == 1 and predicted == 0:
                fn += 1

        total = tp + tn + fp + fn

        accuracy = (
            (tp + tn) / total
            if total else 0
        )

        precision = (
            tp / (tp + fp)
            if tp + fp else 0
        )

        recall = (
            tp / (tp + fn)
            if tp + fn else 0
        )

        f1 = (
            2 * precision * recall
            / (precision + recall)
            if precision + recall
            else 0
        )

        return {
            "true_positive": tp,
            "true_negative": tn,
            "false_positive": fp,
            "false_negative": fn,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4)
        }
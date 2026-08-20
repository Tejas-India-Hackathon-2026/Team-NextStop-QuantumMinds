# services/moving_average.py

def calculate_moving_average(amounts, window=5):

    if not amounts:
        return 0.0

    recent = amounts[-window:]

    return sum(recent) / len(recent)


def compare_with_average(current_amount, average):

    if average == 0:
        return 0.0

    percentage_difference = (
        (current_amount - average) / average
    ) * 100

    return round(percentage_difference, 2)


def detect_unusual_spending(
    current_amount,
    average,
    threshold=200
):

    difference = compare_with_average(
        current_amount,
        average
    )

    return {
        "percentage_difference": difference,
        "unusual": abs(difference) >= threshold
    }
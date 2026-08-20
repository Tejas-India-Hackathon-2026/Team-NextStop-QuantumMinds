def explain_transaction(transaction):

    reasons = []

    if transaction["new_recipient"] == 1:
        reasons.append("New recipient")

    if transaction["previous_connection"] == 0:
        reasons.append("No previous connection")

    if transaction["device_match"] == 0:
        reasons.append("Unknown device")

    if transaction["name_match"] == 0:
        reasons.append("UPI name mismatch")

    if transaction["location_change_km"] > 100:
        reasons.append("Unusual location change")

    if transaction["amount_deviation"] > 2:
        reasons.append("Unusual transaction amount")

    if transaction["hour"] < 5 or transaction["hour"] > 23:
        reasons.append("Unusual transaction time")

    if transaction["velocity"] > 10:
        reasons.append("High transaction velocity")

    return reasons
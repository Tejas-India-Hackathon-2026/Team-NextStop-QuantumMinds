# services/features.py

def create_features(transaction, z_score):
    return [
        transaction.amount,
        z_score,
        transaction.failed_attempts,
        int(transaction.new_device),
        int(transaction.new_location),
        transaction.transaction_hour,
        transaction.previous_transaction_amount,
        transaction.average_transaction_amount
    ]
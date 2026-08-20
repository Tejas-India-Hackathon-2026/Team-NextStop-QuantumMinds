# services/duplicate_detector.py

import hashlib
import time


class DuplicateDetector:

    def __init__(self, expiry_seconds=120):

        self.expiry_seconds = expiry_seconds
        self.transactions = {}

    def create_fingerprint(
        self,
        user_id,
        receiver_id,
        amount
    ):

        raw = (
            f"{user_id}|"
            f"{receiver_id}|"
            f"{amount}"
        )

        return hashlib.sha256(
            raw.encode()
        ).hexdigest()

    def is_duplicate(
        self,
        user_id,
        receiver_id,
        amount
    ):

        fingerprint = self.create_fingerprint(
            user_id,
            receiver_id,
            amount
        )

        now = time.time()

        old_time = self.transactions.get(
            fingerprint
        )

        self.transactions[fingerprint] = now

        if old_time is None:
            return False

        return (
            now - old_time
            <= self.expiry_seconds
        )
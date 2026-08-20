# security/pin_monitor.py

from datetime import datetime, timedelta


class PINAttemptMonitor:

    def __init__(
        self,
        max_attempts=3,
        lock_minutes=10
    ):

        self.max_attempts = max_attempts
        self.lock_minutes = lock_minutes
        self.users = {}

    def failed_attempt(self, user_id):

        now = datetime.utcnow()

        record = self.users.setdefault(
            user_id,
            {
                "attempts": 0,
                "locked_until": None
            }
        )

        record["attempts"] += 1

        if record["attempts"] >= self.max_attempts:

            record["locked_until"] = (
                now
                + timedelta(
                    minutes=self.lock_minutes
                )
            )

        return record

    def is_locked(self, user_id):

        record = self.users.get(user_id)

        if not record:
            return False

        locked_until = record["locked_until"]

        if not locked_until:
            return False

        if datetime.utcnow() < locked_until:
            return True

        record["attempts"] = 0
        record["locked_until"] = None

        return False

    def successful_login(self, user_id):

        self.users.pop(
            user_id,
            None
        )
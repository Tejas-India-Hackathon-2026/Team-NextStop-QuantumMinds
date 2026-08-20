# security/audit.py

from datetime import datetime
import json


class AuditLogger:

    def __init__(self, file_path="audit.log"):

        self.file_path = file_path

    def record(
        self,
        user_id,
        transaction_id,
        event,
        details
    ):

        entry = {
            "timestamp":
                datetime.utcnow().isoformat(),

            "user_id":
                user_id,

            "transaction_id":
                transaction_id,

            "event":
                event,

            "details":
                details
        }

        with open(
            self.file_path,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                json.dumps(entry)
                + "\n"
            )

        return entry
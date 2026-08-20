# security/session_manager.py

import secrets
from datetime import datetime, timedelta


class SessionManager:

    def __init__(self):

        self.sessions = {}

    def create_session(
        self,
        user_id,
        device_id
    ):

        session_id = secrets.token_urlsafe(32)

        self.sessions[session_id] = {
            "user_id": user_id,
            "device_id": device_id,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow()
        }

        return session_id

    def validate_session(
        self,
        session_id,
        timeout_minutes=30
    ):

        session = self.sessions.get(session_id)

        if not session:
            return False

        elapsed = (
            datetime.utcnow()
            - session["last_activity"]
        )

        if elapsed > timedelta(
            minutes=timeout_minutes
        ):

            del self.sessions[session_id]

            return False

        session["last_activity"] = datetime.utcnow()

        return True

    def revoke(self, session_id):

        self.sessions.pop(
            session_id,
            None
        )
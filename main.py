# services/auth.py

from datetime import datetime, timedelta, timezone

from jose import jwt

SECRET_KEY = "CHANGE_THIS_SECRET_KEY"
ALGORITHM = "HS256"


def create_access_token(user_id: str):

    expires = datetime.now(timezone.utc) + timedelta(hours=1)

    payload = {
        "sub": user_id,
        "exp": expires
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
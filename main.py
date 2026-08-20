# security/rate_limiter.py

import time


class RateLimiter:

    def __init__(
        self,
        max_requests=30,
        window_seconds=60
    ):

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    def allow(self, client_id):

        now = time.time()

        timestamps = self.requests.get(
            client_id,
            []
        )

        timestamps = [
            timestamp
            for timestamp in timestamps
            if now - timestamp
            < self.window_seconds
        ]

        if len(timestamps) >= self.max_requests:

            self.requests[client_id] = timestamps

            return False

        timestamps.append(now)

        self.requests[client_id] = timestamps

        return True
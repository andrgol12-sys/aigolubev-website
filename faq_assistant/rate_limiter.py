import time
from collections import defaultdict, deque
from threading import Lock


class RateLimiter:
    def __init__(self, max_requests=5, period_seconds=60):
        self.max_requests = max_requests
        self.period_seconds = period_seconds
        self.requests = defaultdict(deque)
        self.lock = Lock()

    def can_allow(self, session_id):
        now = time.monotonic()

        with self.lock:
            history = self.requests[session_id]

            while history and now - history[0] >= self.period_seconds:
                history.popleft()

            return len(history) < self.max_requests

    def is_allowed(self, session_id):
        now = time.monotonic()

        with self.lock:
            history = self.requests[session_id]

            while history and now - history[0] >= self.period_seconds:
                history.popleft()

            if len(history) >= self.max_requests:
                return False

            history.append(now)
            return True
from threading import Lock

from faq_assistant.rate_limiter import RateLimiter
from faq_assistant.daily_limiter import DailyLimiter


class RequestGuard:
    def __init__(self):
        self.minute_limiter = RateLimiter(
            max_requests=5,
            period_seconds=60
        )
        self.daily_limiter = DailyLimiter(
            max_per_visitor=30,
            max_total=200
        )
        self.lock = Lock()

    def is_allowed(self, session_id):
        with self.lock:
            if not self.minute_limiter.can_allow(session_id):
                return False

            if not self.daily_limiter.can_allow(session_id):
                return False

            if not self.minute_limiter.is_allowed(session_id):
                return False

            return self.daily_limiter.is_allowed(session_id)
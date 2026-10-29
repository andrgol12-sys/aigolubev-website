from datetime import date
from threading import Lock


class DailyLimiter:
    def __init__(self, max_per_visitor=30, max_total=200):
        self.max_per_visitor = max_per_visitor
        self.max_total = max_total
        self.current_day = date.today()
        self.visitor_counts = {}
        self.total_count = 0
        self.lock = Lock()

    def can_allow(self, session_id):
        with self.lock:
            today = date.today()

            if today != self.current_day:
                return True

            if self.total_count >= self.max_total:
                return False

            visitor_count = self.visitor_counts.get(session_id, 0)

            return visitor_count < self.max_per_visitor

    def is_allowed(self, session_id):
        with self.lock:
            today = date.today()

            if today != self.current_day:
                self.current_day = today
                self.visitor_counts.clear()
                self.total_count = 0

            if self.total_count >= self.max_total:
                return False

            visitor_count = self.visitor_counts.get(session_id, 0)

            if visitor_count >= self.max_per_visitor:
                return False

            self.visitor_counts[session_id] = visitor_count + 1
            self.total_count += 1

            return True
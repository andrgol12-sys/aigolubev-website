import sqlite3
from contextlib import closing
import time
from datetime import datetime, timezone
from pathlib import Path


class SQLiteLimiter:
    def __init__(
        self,
        db_path="instance/faq_limits.db",
        max_per_minute=5,
        max_per_day=30,
        max_total_per_day=200,
    ):
        self.db_path = str(db_path)
        self.max_per_minute = max_per_minute
        self.max_per_day = max_per_day
        self.max_total_per_day = max_total_per_day

        Path(self.db_path).parent.mkdir(
            parents=True, exist_ok=True
        )
        self._init_db()

    def _connect(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=10
        )
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    def _init_db(self):
        with closing(self._connect()) as connection, connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS faq_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visitor_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    day_utc TEXT NOT NULL
                )
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_faq_visitor_time
                ON faq_requests (visitor_id, created_at)
            """)

            connection.execute("""
                CREATE INDEX IF NOT EXISTS idx_faq_day
                ON faq_requests (day_utc)
            """)

    def is_allowed(self, visitor_id):
        if not isinstance(visitor_id, str) or not visitor_id:
            return False

        with closing(self._connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")

            now = time.time()
            today = datetime.fromtimestamp(
                now, timezone.utc
            ).date().isoformat()

            connection.execute(
                "DELETE FROM faq_requests WHERE day_utc < ?",
                (today,)
            )

            minute_count = connection.execute(
                """
                SELECT COUNT(*) FROM faq_requests
                WHERE visitor_id = ?
                AND created_at > ?
                """,
                (visitor_id, now - 60)
            ).fetchone()[0]

            day_count = connection.execute(
                """
                SELECT COUNT(*) FROM faq_requests
                WHERE visitor_id = ?
                AND day_utc = ?
                """,
                (visitor_id, today)
            ).fetchone()[0]

            total_count = connection.execute(
                """
                SELECT COUNT(*) FROM faq_requests
                WHERE day_utc = ?
                """,
                (today,)
            ).fetchone()[0]

            if (
                minute_count >= self.max_per_minute
                or day_count >= self.max_per_day
                or total_count >= self.max_total_per_day
            ):
                return False

            connection.execute(
                """
                INSERT INTO faq_requests (
                    visitor_id, created_at, day_utc
                )
                VALUES (?, ?, ?)
                """,
                (visitor_id, now, today)
            )

            return True
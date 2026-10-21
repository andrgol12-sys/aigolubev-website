
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class DatabaseLogger:
    """Записывает технические события сайта в SQLite."""

    ALLOWED_EVENTS = {
        "http.request_completed",
        "contact.created",
        "contact.save_failed",
        "admin.login_succeeded",
        "admin.login_failed",
        "telegram.send_failed",
        "application.error",
    }

    ALLOWED_LEVELS = {"INFO", "WARNING", "ERROR"}

    def __init__(self, db_path="instance/logs.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        with sqlite3.connect(self.db_path, timeout=5) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS log_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    level TEXT NOT NULL,
                    event TEXT NOT NULL,
                    route TEXT,
                    status_code INTEGER,
                    duration_ms INTEGER
                )
            """)

    def log_event(
        self,
        event,
        level="INFO",
        route=None,
        status_code=None,
        duration_ms=None,
    ):
        """Сохраняет событие без пользовательских данных."""

        if event not in self.ALLOWED_EVENTS:
            raise ValueError("Недопустимый тип события")

        if level not in self.ALLOWED_LEVELS:
            raise ValueError("Недопустимый уровень логирования")

        created_at = datetime.now(timezone.utc).isoformat()

        try:
            with sqlite3.connect(self.db_path, timeout=5) as conn:
                conn.execute(
                    """
                    INSERT INTO log_events
                    (created_at, level, event, route,
                     status_code, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        created_at,
                        level,
                        event,
                        route,
                        status_code,
                        duration_ms,
                    ),
                )
        except sqlite3.Error:
            logging.getLogger(__name__).warning(
                "Не удалось сохранить техническое событие"
            )

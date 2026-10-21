
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone


# Путь к базе технических логов
DB_PATH = Path(__file__).resolve().parent / "instance" / "logs.db"


def get_metrics(days=None):
    """Рассчитывает показатели сайта по техническим логам."""

    if not DB_PATH.exists():
        print("База логов пока не создана.")
        return

    # Определяем начало периода для расчёта метрик
    date_from = None

    if days is not None:
        if days <= 0:
            raise ValueError("Количество дней должно быть больше нуля")

        date_from = (
            datetime.now(timezone.utc) - timedelta(days=days)
        ).isoformat()

    with sqlite3.connect(DB_PATH) as conn:

        # Количество успешно созданных заявок
        contacts_created = conn.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE event = ?
              AND (? IS NULL OR created_at >= ?)
            """,
            ("contact.created", date_from, date_from)
        ).fetchone()[0]

        # Количество ошибок сохранения заявок
        contacts_failed = conn.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE event = ?
              AND (? IS NULL OR created_at >= ?)
            """,
            ("contact.save_failed", date_from, date_from)
        ).fetchone()[0]

        # Неудачные попытки входа администратора
        login_failed = conn.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE event = ?
              AND (? IS NULL OR created_at >= ?)
            """,
            ("admin.login_failed", date_from, date_from)
        ).fetchone()[0]

        
        # Среднее время обработки HTTP-запросов
        avg_duration = conn.execute(
            """
            SELECT AVG(duration_ms)
            FROM log_events
            WHERE event = 'http.request_completed'
              AND duration_ms IS NOT NULL
              AND (? IS NULL OR created_at >= ?)
            """,
            (date_from, date_from)
        ).fetchone()[0]

        
        # Количество HTTP-запросов
        total_requests = conn.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE event = 'http.request_completed'
              AND (? IS NULL OR created_at >= ?)
            """,
            (date_from, date_from)
        ).fetchone()[0]

        
        # Количество HTTP-ошибок (статусы 400 и выше)
        error_requests = conn.execute(
            """
            SELECT COUNT(*)
            FROM log_events
            WHERE event = 'http.request_completed'
              AND status_code >= 400
              AND (? IS NULL OR created_at >= ?)
            """,
            (date_from, date_from)
        ).fetchone()[0]

    error_rate = (
        error_requests / total_requests * 100
        if total_requests > 0 else 0
    )

    print("\n=== МЕТРИКИ САЙТА AIGOLUBEV ===")
    print(f"Создано заявок: {contacts_created}")
    print(f"Ошибок сохранения заявок: {contacts_failed}")
    print(f"Неудачных входов администратора: {login_failed}")
    print(f"Всего HTTP-запросов: {total_requests}")
    print(f"Среднее время обработки: {avg_duration or 0:.2f} мс")
    print(f"HTTP Error Rate: {error_rate:.2f}%")
    print("==============================\n")


if __name__ == "__main__":
    get_metrics()

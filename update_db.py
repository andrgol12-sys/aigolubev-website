
import sqlite3

DB_PATH = "instance/aigolubev.db"

connection = sqlite3.connect(DB_PATH)

try:
    # Проверяем существующие столбцы таблицы
    cursor = connection.execute("PRAGMA table_info(contact_requests)")
    columns = {row[1] for row in cursor.fetchall()}

    if not columns:
        raise RuntimeError("Таблица contact_requests не найдена!")

    # Добавляем дату и время согласия
    if "consent_at" not in columns:
        connection.execute(
            "ALTER TABLE contact_requests ADD COLUMN consent_at DATETIME"
        )
        print("Добавлен столбец consent_at")
    else:
        print("Столбец consent_at уже существует")

    # Добавляем редакцию согласия
    if "consent_version" not in columns:
        connection.execute(
            "ALTER TABLE contact_requests ADD COLUMN consent_version VARCHAR(20)"
        )
        print("Добавлен столбец consent_version")
    else:
        print("Столбец consent_version уже существует")

    connection.commit()

    # Проверяем количество заявок
    cursor = connection.execute(
        "SELECT COUNT(*) FROM contact_requests"
    )
    print(f"Всего заявок в базе: {cursor.fetchone()[0]}")

    print("Обновление базы завершено успешно!")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()

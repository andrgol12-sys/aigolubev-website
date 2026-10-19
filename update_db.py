import sqlite3

connection = sqlite3.connect("instance/aigolubev.db")

try:
    cursor = connection.execute(
        "SELECT id, status FROM contact_requests ORDER BY id"
    )

    requests = cursor.fetchall()

    print(f"Всего заявок: {len(requests)}")

    for request_id, status in requests:
        print(f"Заявка №{request_id}: {status}")

finally:
    connection.close()
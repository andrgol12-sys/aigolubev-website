
import os
import requests

from dotenv import load_dotenv

# Загружаем настройки из файла .env
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_test_message():
    if not BOT_TOKEN or not CHAT_ID:
        print("Ошибка: проверьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    message = (
        "✅ AIGolubev\n\n"
        "Тестовое уведомление из Python!\n\n"
        "Telegram-бот успешно подключён к сайту."
    )

    try:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )

        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
            print("Успешно! Сообщение отправлено в Telegram.")
        else:
            print("Telegram не подтвердил отправку сообщения.")

    except requests.RequestException as error:
        print(f"Ошибка отправки: {type(error).__name__}")
        print("Проверьте подключение к интернету и настройки Telegram.")


if __name__ == "__main__":
    send_test_message()

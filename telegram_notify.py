
import os
import logging
import requests

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def send_telegram_notification(request_id, subject):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    site_url = os.getenv("SITE_URL", "").rstrip("/")

    if not bot_token or not chat_id:
        logger.warning("Telegram: отсутствуют настройки подключения.")
        return False

    message = (
        "🔔 Новая заявка на сайте AIGolubev!\n\n"
        f"Номер заявки: {request_id}\n"
        f"Тема: {subject}\n\n"
        "Откройте административную панель для просмотра."
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
    "chat_id": chat_id,
    "text": message,
    "reply_markup": {
        "inline_keyboard": [
            [
                {
                    "text": "📋 Открыть заявку",
                    "url": f"{site_url}/admin"
                }
            ]
        ]
    }
},
            timeout=5
        )

        response.raise_for_status()

        if response.json().get("ok"):
            return True

        logger.warning("Telegram не подтвердил отправку уведомления.")
        return False

    except (requests.RequestException, ValueError):
        logger.exception("Не удалось отправить уведомление в Telegram.")
        return False

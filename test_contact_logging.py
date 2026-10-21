
from unittest.mock import patch, MagicMock
from flask import url_for

from app import app


def test_contact_logging():
    # Используем тестовый клиент Flask
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        # Подменяем сохранение в БД, Telegram и логгер
        with patch("app.db.session.add"), \
             patch("app.db.session.commit"), \
             patch("app.send_telegram_notification"), \
             patch("app.logger.log_event") as mock_log, \
             patch("app.ContactForm") as mock_form:

            form = MagicMock()
            form.validate_on_submit.return_value = True
            form.name.data = "Тест"
            form.email.data = "test@example.com"
            form.phone.data = None
            form.subject.data = "Проверка"
            form.message.data = "Тестовое сообщение"
            mock_form.return_value = form

            response = client.post("/")

            assert response.status_code == 302
            mock_log.assert_any_call(
                event="contact.created",
                level="INFO",
                route="/",
            )

    print("PASS: событие contact.created вызывается автоматически")


if __name__ == "__main__":
    test_contact_logging()

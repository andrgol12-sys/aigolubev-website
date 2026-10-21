
from unittest.mock import patch, MagicMock

from sqlalchemy.exc import SQLAlchemyError

from app import app


def test_contact_save_error():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        with patch("app.db.session.add"), \
             patch("app.db.session.commit", side_effect=SQLAlchemyError("Test error")), \
             patch("app.db.session.rollback") as mock_rollback, \
             patch("app.send_telegram_notification") as mock_telegram, \
             patch("app.logger.log_event") as mock_log, \
             patch("app.ContactForm") as mock_form:

            form = MagicMock()
            form.validate_on_submit.return_value = True
            form.name.data = "Тест"
            form.email.data = "test@example.com"
            form.phone.data = None
            form.subject.data = "Проверка ошибки"
            form.message.data = "Тестовое сообщение"
            mock_form.return_value = form

            response = client.post("/")

            assert response.status_code == 302
            mock_rollback.assert_called_once()
            mock_log.assert_any_call(
                event="contact.save_failed",
                level="ERROR",
                route="/",
            )
            mock_telegram.assert_not_called()

    print("PASS: ошибка сохранения заявки обработана корректно")


if __name__ == "__main__":
    test_contact_save_error()

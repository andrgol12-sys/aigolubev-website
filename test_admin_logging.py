
from unittest.mock import patch, MagicMock

from app import app


def test_admin_logging():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    # Создаём имитацию администратора
    fake_admin = MagicMock()
    fake_admin.check_password.return_value = True

    # Контекст приложения необходим для Flask-SQLAlchemy
    with app.app_context():
        with app.test_client() as client:
            with patch("app.AdminLoginForm") as mock_form, \
                 patch("app.AdminUser.query") as mock_query, \
                 patch("app.login_user") as mock_login, \
                 patch("app.logger.log_event") as mock_log:

                form = MagicMock()
                form.validate_on_submit.return_value = True
                form.username.data = "test_admin"
                form.password.data = "test_password"
                mock_form.return_value = form

                mock_query.filter_by.return_value.first.return_value = fake_admin

                # Сценарий 1: успешный вход
                response = client.post("/admin/login")

                assert response.status_code == 302
                mock_login.assert_called_once()
                mock_log.assert_any_call(
                    event="admin.login_succeeded",
                    level="INFO",
                    route="/admin/login",
                )

                # Сценарий 2: неправильный пароль
                mock_log.reset_mock()
                fake_admin.check_password.return_value = False

                response = client.post("/admin/login")

                assert response.status_code == 200
                mock_log.assert_any_call(
                    event="admin.login_failed",
                    level="WARNING",
                    route="/admin/login",
                )

    print("PASS: логирование успешного и неудачного входа работает")


if __name__ == "__main__":
    test_admin_logging()

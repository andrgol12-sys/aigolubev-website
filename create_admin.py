
import getpass

from app import app
from models import db, AdminUser


with app.app_context():
    username = input("Введите логин администратора: ").strip()

    if not username:
        print("Ошибка: логин не может быть пустым.")

    elif AdminUser.query.filter_by(username=username).first():
        print("Ошибка: администратор с таким логином уже существует.")

    else:
        password = getpass.getpass("Введите пароль: ")
        password_confirm = getpass.getpass("Повторите пароль: ")

        if len(password) < 12:
            print("Ошибка: пароль должен содержать минимум 12 символов.")

        elif password != password_confirm:
            print("Ошибка: пароли не совпадают.")

        else:
            admin = AdminUser(username=username)
            admin.set_password(password)

            db.session.add(admin)
            db.session.commit()

            print(f"Администратор '{username}' успешно создан!")

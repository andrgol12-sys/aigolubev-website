
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Email, Length, Optional


class ContactForm(FlaskForm):
    name = StringField(
        "Ваше имя",
        validators=[
            DataRequired(message="Укажите ваше имя."),
            Length(
                min=2,
                max=100,
                message="Имя должно содержать от 2 до 100 символов."
            )
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Укажите адрес электронной почты."),
            Email(message="Введите корректный адрес электронной почты."),
            Length(
                max=255,
                message="Email не должен превышать 255 символов."
            )
        ]
    )

    phone = StringField(
        "Телефон (необязательно)",
        validators=[
            Optional(),
            Length(
                max=30,
                message="Телефон не должен превышать 30 символов."
            )
        ]
    )

    subject = StringField(
        "Тема обращения",
        validators=[
            DataRequired(message="Укажите тему обращения."),
            Length(
                min=3,
                max=200,
                message="Тема должна содержать от 3 до 200 символов."
            )
        ]
    )

    message = TextAreaField(
        "Описание задачи",
        validators=[
            DataRequired(message="Опишите вашу задачу."),
            Length(
                min=10,
                max=5000,
                message="Описание должно содержать от 10 до 5000 символов."
            )
        ]
    )

    submit = SubmitField("Отправить заявку")

    
class AdminLoginForm(FlaskForm):
    username = StringField(
        "Логин",
        validators=[
            DataRequired(message="Введите логин.")
        ]
    )

    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Введите пароль.")
        ]
    )

    submit = SubmitField("Войти")


import os

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, ContactRequest, AdminUser
from forms import ContactForm, AdminLoginForm
from telegram_notify import send_telegram_notification
from datetime import datetime, timezone

app = Flask(__name__)

# Секретный ключ для защиты форм и сессий
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-local-key")

# Настройки базы данных
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///aigolubev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Защита POST-форм от CSRF-атак
csrf = CSRFProtect(app)


# Настройка авторизации администраторов
login_manager = LoginManager()
login_manager.init_app(app)

# Страница входа для неавторизованных пользователей
login_manager.login_view = "admin_login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(AdminUser, int(user_id))


@app.route("/", methods=["GET", "POST"])
def home():
    form = ContactForm()

    if form.validate_on_submit():
        request_data = ContactRequest(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data or None,
            subject=form.subject.data,
            message=form.message.data,
            consent_at=datetime.now(timezone.utc),
            consent_version="1.1"
        )

        db.session.add(request_data)
        db.session.commit()

        # Отправляем уведомление о новой заявке в Telegram
        send_telegram_notification(
            request_id=request_data.id,
            subject=request_data.subject
        )

        flash("Ваша заявка успешно отправлена!", "success")

        return redirect(url_for("home", _anchor="contacts"))

    return render_template("index.html", form=form)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    # Если администратор уже вошёл, открываем панель
    if current_user.is_authenticated:
        return redirect(url_for("admin_dashboard"))

    form = AdminLoginForm()

    if form.validate_on_submit():
        admin = AdminUser.query.filter_by(
            username=form.username.data.strip()
        ).first()

        if admin and admin.check_password(form.password.data):
            login_user(admin)
            return redirect(url_for("admin_dashboard"))

        flash("Неверный логин или пароль.", "error")

    return render_template("admin/login.html", form=form)



@app.route("/admin")
@login_required
def admin_dashboard():
    from flask import request
    from sqlalchemy import or_

    # Получаем параметры поиска и фильтрации
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")
    work_status_filter = request.args.get("work_status", "all")

    # Счётчики по всем заявкам
    total_count = ContactRequest.query.count()
    unread_count = ContactRequest.query.filter_by(is_read=False).count()

    # Формируем запрос к базе данных
    query = ContactRequest.query

    # Фильтр непрочитанных
    if status_filter == "unread":
        query = query.filter_by(is_read=False)
    else:
        status_filter = "all"

    # Фильтрация по этапу обработки
    allowed_work_statuses = {"new", "in_progress", "completed"}

    if work_status_filter in allowed_work_statuses:
        query = query.filter_by(status=work_status_filter)
    else:
        work_status_filter = "all"

    # Поиск по данным заявки
    if search_query:
        search_pattern = f"%{search_query}%"

        query = query.filter(
            or_(
                ContactRequest.name.ilike(search_pattern),
                ContactRequest.email.ilike(search_pattern),
                ContactRequest.phone.ilike(search_pattern),
                ContactRequest.subject.ilike(search_pattern),
                ContactRequest.message.ilike(search_pattern),
            )
        )

    # Сортировка: сначала новые заявки
    requests = query.order_by(
        ContactRequest.created_at.desc()
    ).all()

    return render_template(
        "admin/dashboard.html",
        requests=requests,
        total_count=total_count,
        unread_count=unread_count,
        status_filter=status_filter,
        search_query=search_query,
        work_status_filter=work_status_filter,
    )

@app.route("/consent")
def consent():
    return render_template("consent.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/admin/logout", methods=["POST"])
@login_required
def admin_logout():
    logout_user()
    flash("Вы успешно вышли из административной панели.", "success")
    return redirect(url_for("admin_login"))


@app.route("/admin/request/<int:request_id>/toggle-read", methods=["POST"])
@login_required
def toggle_request_read(request_id):
    request_data = db.get_or_404(ContactRequest, request_id)

    # Переключаем статус заявки
    request_data.is_read = not request_data.is_read

    db.session.commit()

    return redirect(url_for("admin_dashboard"))

@app.route("/admin/request/<int:request_id>/status", methods=["POST"])
@login_required
def update_request_status(request_id):
    from flask import request

    request_data = db.get_or_404(ContactRequest, request_id)

    # Получаем выбранный статус из формы
    new_status = request.form.get("status")

    # Разрешённые статусы
    allowed_statuses = {"new", "in_progress", "completed"}

    if new_status not in allowed_statuses:
        flash("Недопустимый статус заявки.", "error")
        return redirect(url_for("admin_dashboard"))

    # Сохраняем новый статус в базе данных
    request_data.status = new_status
    db.session.commit()

    flash("Статус заявки успешно обновлён.", "success")

    return redirect(url_for("admin_dashboard"))


# Создание таблиц базы данных
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from flask_wtf.csrf import CSRFProtect
from faq_assistant.visitor_identity import get_visitor_id
from faq_assistant.sqlite_limiter import SQLiteLimiter
from faq_assistant.privacy import contains_contact_data
from faq_assistant.chat import FAQChat
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, ContactRequest, AdminUser
from sqlalchemy.exc import SQLAlchemyError
from forms import ContactForm, AdminLoginForm
from telegram_notify import send_telegram_notification
from datetime import datetime, timezone
import time
from flask import g
from db_logger import DatabaseLogger

app = Flask(__name__)

# Инициализация технического логирования
logger = DatabaseLogger(
    db_path=os.path.join(app.instance_path, "logs.db")
)

# Начало обработки HTTP-запроса
@app.before_request
def start_request_timer():
    g.request_start_time = time.perf_counter()


# Завершение обработки HTTP-запроса
@app.after_request
def log_request(response):
    start_time = getattr(g, "request_start_time", None)

    if start_time is not None:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000
        )

        # Используем шаблон маршрута, а не URL с параметрами
        route = (
            request.url_rule.rule
            if request.url_rule
            else "unmatched"
        )

        logger.log_event(
            event="http.request_completed",
            level="INFO" if response.status_code < 400 else (
                "WARNING" if response.status_code < 500 else "ERROR"
            ),
            route=route,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

    return response

# Секретный ключ для защиты форм и сессий
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-local-key")

# Защита cookie Flask-сессий
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

# Настройки базы данных
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///aigolubev.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Защита POST-форм от CSRF-атак
csrf = CSRFProtect(app)

# Ограничение количества запросов к FAQ-ассистенту
faq_limiter = SQLiteLimiter(
    db_path=os.path.join(app.instance_path, "faq_limits.db"),
    max_per_minute=5,
    max_per_day=30,
    max_total_per_day=200,
)

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

        try:
            db.session.add(request_data)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()

            logger.log_event(
                event="contact.save_failed",
                level="ERROR",
                route="/",
            )

            flash(
                "Не удалось сохранить заявку. Попробуйте позже.",
                "error",
            )
            return redirect(url_for("home", _anchor="contacts"))

        # Фиксируем успешное создание заявки без персональных данных
        logger.log_event(
            event="contact.created",
            level="INFO",
            route="/",
        )

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

            # Успешный вход администратора
            logger.log_event(
                event="admin.login_succeeded",
                level="INFO",
                route="/admin/login",
            )

            return redirect(url_for("admin_dashboard"))

        # Неудачная попытка входа администратора
        logger.log_event(
            event="admin.login_failed",
            level="WARNING",
            route="/admin/login",
        )

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

faq_assistant = FAQChat()

@app.route("/api/faq/chat", methods=["POST"])
def faq_chat_api():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {
            "success": False,
            "message": "Некорректный формат запроса."
        }, 400

    question = data.get("question")

    if not isinstance(question, str) or not question.strip():
        return {
            "success": False,
            "message": "Пожалуйста, введите вопрос."
        }, 400

    if len(question) > 1000:
        return {
            "success": False,
            "message": "Сократите вопрос до 1000 символов."
        }, 400

    # Не отправляем распознанные контактные данные в ИИ
    if contains_contact_data(question):
        return {
            "success": False,
            "message": (
                "Пожалуйста, не указывайте контактные данные в чате. "
                "Для связи воспользуйтесь формой заявки на сайте AIGolubev."
            )
        }, 400

    visitor_id = get_visitor_id()

    # Проверяем лимиты до обращения к ИИ
    try:
        allowed = faq_limiter.is_allowed(visitor_id)
    except Exception:
        app.logger.exception("FAQ rate limiter error")
        return {
            "success": False,
            "message": "Сервис временно недоступен. Попробуйте позже."
        }, 503

    if not allowed:
        return {
            "success": False,
            "message": "Превышен лимит запросов. Попробуйте позже."
        }, 429

    try:
        answer = faq_assistant.ask(visitor_id, question)
    except Exception:
        app.logger.exception("FAQ assistant error")
        return {
            "success": False,
            "message": "Не удалось получить ответ. Попробуйте позже."
        }, 503

    return {
        "success": True,
        "answer": answer
    }, 200

# Создание таблиц базы данных
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)

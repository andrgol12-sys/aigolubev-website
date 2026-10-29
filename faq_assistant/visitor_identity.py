import secrets

from flask import session


def get_visitor_id():
    """Возвращает идентификатор посетителя Flask-сессии."""

    visitor_id = session.get("faq_visitor_id")

    if not isinstance(visitor_id, str) or len(visitor_id) != 64:
        visitor_id = secrets.token_hex(32)
        session["faq_visitor_id"] = visitor_id

    return visitor_id

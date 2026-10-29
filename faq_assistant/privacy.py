
import re


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+7|8)[\s()\-]*"
    r"(?:\d[\s()\-]*){10}(?!\d)"
)

# Международные номера с кодом страны, например +49 или +1
INTERNATIONAL_PHONE_PATTERN = re.compile(
    r"(?<![\w+])\+(?:\d[\s().\-]*){8,15}(?!\d)"
)

def contains_contact_data(message):
    """Проверяет наличие email или российского телефона."""

    if not isinstance(message, str):
        return False

    return bool(
        EMAIL_PATTERN.search(message)
        or PHONE_PATTERN.search(message)
        or INTERNATIONAL_PHONE_PATTERN.search(message)
    )

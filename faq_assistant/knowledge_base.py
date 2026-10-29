import json
from pathlib import Path


# Путь к файлу базы знаний
FAQ_FILE = Path(__file__).resolve().parent / "data" / "faqs.json"


def load_faqs():
    """Загружает вопросы и ответы из базы знаний."""

    with FAQ_FILE.open("r", encoding="utf-8") as file:
        faqs = json.load(file)

    if not isinstance(faqs, list):
        raise ValueError("База знаний FAQ должна содержать список.")

    return faqs

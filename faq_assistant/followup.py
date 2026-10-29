"""Распознавание типичных уточняющих вопросов посетителя."""

import re


FOLLOWUP_PATTERNS = {
    "price": [
        r"\bсколько\s+(?:это\s+)?стоит\b",
        r"\bкакая\s+(?:будет\s+)?стоимость\b",
        r"\bсколько\s+будет\s+стоить\b",
    ],
    "timeline": [
        r"\bкакие\s+сроки\b",
        r"\bсколько\s+(?:это\s+)?времени\s+займ[её]т\b",
        r"\bкак\s+долго\b",
    ],
    "details": [
        r"\bрасскажите\s+подробнее\b",
        r"\bможно\s+подробнее\b",
    ],
}


def detect_followup(question):
    """Возвращает тип уточнения или None."""

    if not isinstance(question, str):
        return None

    normalized = question.strip().lower()

    if not normalized or len(normalized) > 100:
        return None

    for category, patterns in FOLLOWUP_PATTERNS.items():
        for pattern in patterns:
            if re.fullmatch(rf"{pattern}[?.!]*", normalized):
                return category

    return None

def is_valid_followup(question, memory):
    """Проверяет, является ли вопрос продолжением диалога."""

    followup_type = detect_followup(question)

    if followup_type is None or memory is None:
        return False

    history = memory.get_history()

    # Ищем последний самостоятельный вопрос посетителя.
    for item in reversed(history):
        if item.get("role") != "user":
            continue

        previous_question = item.get("content", "")

        # Пропускаем промежуточные уточнения.
        if detect_followup(previous_question) is not None:
            continue

        # Проверяем исходную тему разговора.
        from faq_assistant.topic_guard import is_relevant_question

        return is_relevant_question(previous_question)

    return False
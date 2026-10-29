from faq_assistant.search import search_faqs


def is_relevant_question(question):
    """Проверяет, связан ли вопрос с базой знаний AIGolubev."""

    if not isinstance(question, str) or not question.strip():
        return False

    results = search_faqs(question, limit=1)

    return bool(results)

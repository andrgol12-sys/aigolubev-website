from faq_assistant.generator import generate_answer
from faq_assistant.session_manager import ConversationManager
from faq_assistant.privacy import contains_contact_data
from faq_assistant.topic_guard import is_relevant_question
from faq_assistant.followup import is_valid_followup


class FAQChat:
    """Управляет перепиской с FAQ-ассистентом."""

    def __init__(self):
        self.manager = ConversationManager()

    def ask(self, session_id, question):
        """Обрабатывает вопрос и сохраняет историю диалога."""

        if not isinstance(question, str) or not question.strip():
            return "Пожалуйста, введите вопрос."

        if len(question) > 1000:
            return (
                "Ваше сообщение слишком длинное. "
                "Пожалуйста, сократите вопрос до 1000 символов."
            )

        if contains_contact_data(question):
            return (
                "Пожалуйста, не указывайте контактные данные "
                "в чате. Для связи воспользуйтесь формой "
                "заявки на сайте AIGolubev."
            )

        memory = self.manager.get_memory(session_id)

        relevant = is_relevant_question(question)

        if not relevant:
            relevant = is_valid_followup(question, memory)

        if not relevant:
            memory.clear()
            return (
                "Я консультирую по услугам AIGolubev: "
                "разработке чат-ботов, AI-ассистентов "
                "и автоматизации бизнеса. "
                "Буду рад помочь с вопросами по этим направлениям."
            )

        answer = generate_answer(question, memory=memory)

        memory.add_message("user", question)
        memory.add_message("assistant", answer)

        return answer

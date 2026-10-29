from faq_assistant.memory import ConversationMemory


class ConversationManager:
    """Управляет памятью отдельных диалогов."""

    def __init__(self):
        self.sessions = {}

    def get_memory(self, session_id):
        """Возвращает память диалога или создаёт новую."""
        if session_id not in self.sessions:
            self.sessions[session_id] = ConversationMemory()

        return self.sessions[session_id]

    def clear_session(self, session_id):
        """Удаляет историю указанного диалога."""
        self.sessions.pop(session_id, None)

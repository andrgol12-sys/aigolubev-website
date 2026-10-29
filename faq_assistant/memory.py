
from collections import deque


class ConversationMemory:
    """Хранит последние сообщения текущего диалога."""

    def __init__(self, max_messages=20):
        self.messages = deque(maxlen=max_messages)

    def add_message(self, role, content):
        """Добавляет сообщение в историю."""
        self.messages.append({
            "role": role,
            "content": content,
        })

    def get_history(self):
        """Возвращает историю сообщений."""
        return list(self.messages)

    def clear(self):
        """Очищает историю диалога."""
        self.messages.clear()

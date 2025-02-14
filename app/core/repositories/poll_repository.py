
from app.core.entities.poll import Poll

class PollRepository:
    def __init__(self):
        # Здесь можно реализовать логику подключения к БД
        self.polls = []  # Здесь будут храниться опросы для примера

    def save(self, poll: Poll):
        """Сохраняет новый опрос."""
        self.polls.append(poll)
    
    def get(self, poll_id: int):
        """Получает опрос по ID."""
        return next((poll for poll in self.polls if poll.id == poll_id), None)

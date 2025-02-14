from datetime import datetime, timedelta
from app.core.entities.poll import Poll

class CreatePollUseCase:
    def __init__(self):
        self.polls = {}

    async def execute(self, question: str, options: list, duration_minutes: int):
        if not question or not options:
            raise ValueError("Вопрос или варианты ответа не могут быть пустыми.")
        
        """
        Создает опрос с указанным временем окончания.
        """
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        poll = Poll(question=question, options=options, end_time=end_time)
        return poll
    
    async def save_poll(self, poll_id: str, poll: Poll):
        """
        Сохраняет опрос в хранилище.
        """
        self.polls[poll_id] = poll

    async def get_poll(self, poll_id: str) -> Poll:
        """
        Получает опрос из хранилища по его идентификатору.
        """
        return self.polls.get(poll_id)

    async def delete_poll(self, poll_id: str):
        """
        Удаляет опрос из хранилища.
        """
        if poll_id in self.polls:
            del self.polls[poll_id]
    
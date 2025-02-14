from datetime import datetime, timedelta
from app.core.entities.poll import Poll

class PollService:
    async def create_poll(self, question: str, options: list[str], duration_minutes: int) -> Poll:
        """
        Создает опрос с указанным временем окончания.
        """
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        return Poll(question=question, options=options, end_time=end_time)

    async def close_poll(self, poll: Poll) -> Poll:
        """
        Закрывает опрос.
        """
        poll.is_closed = True
        return poll
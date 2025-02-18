from app.core.services.poll_service import PollService

class CreatePollUseCase:
    def __init__(self, poll_service: PollService):
        self.poll_service = poll_service

    async def execute(self, chat_id: int, place_name: str, end_time: str):
        poll_message = await self.poll_service.send_poll(chat_id, place_name, end_time)
        
        if not hasattr(poll_message, "message_id"):
            raise ValueError("Опрос не был успешно создан: отсутствует message_id")
        
        return {
            "chat_id": chat_id,
            "place_name": place_name,
            "end_time": end_time,
            "message_id": poll_message.message_id
        }

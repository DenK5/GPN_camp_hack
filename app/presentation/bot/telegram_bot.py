import logging
from aiogram import Bot, Dispatcher
from app.presentation.bot.handlers import user_handler

class TelegramBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher()

    async def send_message(self, chat_id: int, text: str):
        try:
            await self.bot.send_message(chat_id, text)
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {e}")
    
    async def send_poll(self, chat_id: int, question: str, options: list):
        try:
            poll_message = await self.bot.send_poll(chat_id, question, options)
            return poll_message
        except Exception as e:
            logging.error(f"Ошибка при отправке опроса: {e}")
            return None

    async def register_handlers(self):
        user_handler.register_user_handlers(self.dp)

    async def setup(self):
        await self.dp.start_polling(self.bot)

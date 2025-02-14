import logging
from aiogram import Bot, Dispatcher
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
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

    async def request_office_location(self, message):
        # Создаем кнопку для запроса местоположения
        location_button = KeyboardButton("Отправить местоположение", request_location=True)
        markup = ReplyKeyboardMarkup(resize_keyboard=True).add(location_button)
        await message.answer("Пожалуйста, отправь местоположение своего офиса.", reply_markup=markup)

async def start_bot():
    from app.presentation.bot.telegram_bot import TelegramBot
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

    bot = TelegramBot(token=TOKEN) 
    logging.info("Бот запущен...")

    # Регистрируем обработчики
    await bot.register_handlers()

    # Убираем все предыдущие вебхуки и начинаем опрос
    await bot.bot.delete_webhook(drop_pending_updates=True)
    await bot.dp.start_polling(bot.bot)

if __name__ == "__main__":
    import asyncio
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_bot())

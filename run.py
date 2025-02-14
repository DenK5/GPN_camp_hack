import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

from app.presentation.bot.handlers import user_handler, poll_handler
from app.core.services.poll_service import PollService
from app.core.repositories.poll_repository import PollRepository
from app.core.repositories.restaurant_repository import RestaurantRepository
from app.presentation.bot.telegram_bot import TelegramBot

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

logging.basicConfig(level=logging.INFO)

# Создаем экземпляр бота и диспетчера
bot = TelegramBot(token=TOKEN)
dp = bot.dp  # Диспетчер теперь из объекта TelegramBot

# Создание экземпляра сервиса PollService
poll_repository = PollRepository()
restaurant_repository = RestaurantRepository()
poll_service = PollService(poll_repository, restaurant_repository)

# Регистрируем хендлеры
async def register_handlers():
    user_handler.register_user_handlers(dp)  # Правильный вызов
    poll_handler.register_handlers_poll(dp, poll_service)  # Исправили название функции

async def start_bot():
    # Регистрация обработчиков
    await register_handlers()

    logging.info("Бот запущен...")
    await bot.bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot.bot)

if __name__ == "__main__":
    asyncio.run(start_bot())

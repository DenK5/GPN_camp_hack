import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.presentation.bot.handlers import user_handler, lunch_handler
from app.core.services.poll_service import PollService
from app.core.repositories.poll_repository import PollRepository
from app.core.repositories.restaurant_repository import RestaurantRepository

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

poll_repository = PollRepository()
restaurant_repository = RestaurantRepository()
poll_service = PollService(poll_repository, restaurant_repository)

def register_handlers():
    logging.info("🛠️ Регистрируем обработчики...")
    user_handler.register_user_handlers(dp)
    lunch_handler.register_lunch_handlers(dp, bot)
    logging.info("✅ Все обработчики зарегистрированы!")

async def start_bot():
    register_handlers()
    logging.info("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start_bot())

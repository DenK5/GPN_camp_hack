import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from app.presentation.bot.handlers import user_handler, lunch_handler
from app.core.services.poll_service import PollService

from dotenv import load_dotenv
from config import Config

load_dotenv(override=True)

TOKEN = Config.TELEGRAM_BOT_TOKEN

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

poll_service = PollService()

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

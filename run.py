import asyncio
import logging
import os
from dotenv import load_dotenv

from app.presentation.bot.handlers import user_handler, poll_handler
from app.core.services.poll_service import PollService
from app.core.repositories.poll_repository import PollRepository
from app.core.repositories.restaurant_repository import RestaurantRepository
from app.presentation.bot.telegram_bot import TelegramBot

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в .env файле!")

logging.basicConfig(level=logging.INFO)

bot = TelegramBot(token=TOKEN)

poll_repository = PollRepository()
restaurant_repository = RestaurantRepository()
poll_service = PollService(poll_repository, restaurant_repository)

async def register_handlers():
    await bot.register_handlers()

async def start_bot():
    await register_handlers()

    logging.info("Бот запущен...")
    await bot.setup()

if __name__ == "__main__":
    asyncio.run(start_bot())

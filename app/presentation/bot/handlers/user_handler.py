import logging
from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import ContentType
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from app.core.services.user_service import UserService
from app.presentation.ui.messages import (
    WELCOME_MESSAGE, ASK_CUISINE, ASK_AVG_RECEIPT, ASK_FOOD
)
from aiogram.filters import CommandObject
from app.presentation.bot.handlers.lunch_handler import start_lunch_private
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSurvey(StatesGroup):
    cuisine = State()
    avg_receipt = State()
    food_preferences = State()
    office_location = State()

async def start_command(message: types.Message, state: FSMContext, command: CommandObject):
    """Обрабатывает команду /start, проверяя параметры deep linking."""
    if command.args == "lunch":
        await start_lunch_private(message, state)
        return

    await message.answer(WELCOME_MESSAGE)
    await message.answer(ASK_CUISINE)
    await state.set_state(UserSurvey.cuisine)

async def set_cuisine(message: types.Message, state: FSMContext):
    """Обрабатывает выбор кухни пользователя."""
    await state.update_data(cuisine=message.text)
    await message.answer(ASK_AVG_RECEIPT)
    await state.set_state(UserSurvey.avg_receipt)

async def set_avg_receipt(message: types.Message, state: FSMContext):
    """Обрабатывает среднюю сумму чека."""
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи сумму числом.")
        return
    await state.update_data(avg_receipt=int(message.text))
    await message.answer(ASK_FOOD)
    await state.set_state(UserSurvey.food_preferences)

async def set_food_preferences(message: types.Message, state: FSMContext):
    """Обрабатывает предпочтения по еде."""
    await state.update_data(food_preferences=message.text)
    web_app_url = "https://mycustomname.loca.lt"
    web_app = WebAppInfo(url=web_app_url)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Ввести адрес", web_app=web_app)]],
        resize_keyboard=True
    )
    
    await message.answer("Теперь укажи адрес офиса, где ты работаешь:", reply_markup=keyboard)
    await state.set_state(UserSurvey.office_location)

async def webapp_data_handler(message: types.Message, state: FSMContext):
    """Обрабатываем данные из WebApp."""
    logging.info(f"🔹 Получено сообщение от пользователя {message.from_user.id}")

    if message.web_app_data:
        try:
            logging.info(f"📩 Данные WebApp: {message.web_app_data.data}")
            
            data = json.loads(message.web_app_data.data)
            address = data.get("address")
            
            if not address:
                raise ValueError("Адрес не найден в данных WebApp")
            
            await state.update_data(office_location=address)
            await message.answer(f"Адрес успешно сохранен: {address}")
            await state.clear()
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"❌ Ошибка обработки данных WebApp: {e}")
            await message.answer("❌ Ошибка обработки данных WebApp! Проверьте формат.")
    else:
        logging.warning("❌ WebApp-данные отсутствуют!")
        await message.answer("❌ Данные из WebApp отсутствуют!")

def register_user_handlers(dp: Dispatcher):
    """Регистрирует обработчики команд и состояний."""
    dp.message.register(start_command, Command("start"))
    dp.message.register(set_cuisine, UserSurvey.cuisine)
    dp.message.register(set_avg_receipt, UserSurvey.avg_receipt)
    dp.message.register(set_food_preferences, UserSurvey.food_preferences)
    dp.message.register(webapp_data_handler, UserSurvey.office_location)

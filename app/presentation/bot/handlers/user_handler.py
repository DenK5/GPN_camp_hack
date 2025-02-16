import logging
import json
from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from aiogram.types import ContentType
from aiogram.types import WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, ContentType
from app.core.services.user_service import UserService
from app.presentation.ui.messages import (
    WELCOME_MESSAGE, ASK_CUISINE, ASK_AVG_RECEIPT, ASK_FOOD
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSurvey(StatesGroup):
    cuisine = State()
    avg_receipt = State()
    food_preferences = State()
    office_location = State()

async def start_command(message: types.Message, state: FSMContext):
    await message.answer(WELCOME_MESSAGE)
    await message.answer(ASK_CUISINE)
    await state.set_state(UserSurvey.cuisine)

async def set_cuisine(message: types.Message, state: FSMContext):
    await state.update_data(cuisine=message.text)
    await message.answer(ASK_AVG_RECEIPT)
    await state.set_state(UserSurvey.avg_receipt)

async def set_avg_receipt(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи сумму числом.")
        return
    await state.update_data(avg_receipt=int(message.text))
    await message.answer(ASK_FOOD)
    await state.set_state(UserSurvey.food_preferences)

async def set_food_preferences(message: types.Message, state: FSMContext):
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
    """Обрабатываем данные из WebApp"""
    logging.info(f"🔹 Получено сообщение от пользователя {message.from_user.id}")

    if message.web_app_data:
        try:
            logging.info(f"📩 Данные WebApp: {message.web_app_data.data}")
            data = json.loads(message.web_app_data.data)
            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude and longitude:
                latitude = float(latitude)
                longitude = float(longitude)
                logging.info(f"📍 Координаты: {latitude}, {longitude}")
                
                user_data = await state.get_data()

                async with UserService() as user_service:
                    await user_service.save_user_data(
                        message.from_user.id,
                        user_data['cuisine'],
                        user_data['avg_receipt'],
                        user_data['food_preferences'],
                        latitude,
                        longitude
                    )

                await message.answer(f"✅ Ваш офис сохранен!")
            else:
                logging.warning("❌ Ошибка: координаты не найдены!")
                await message.answer("❌ Ошибка: координаты не найдены!")
        except (json.JSONDecodeError, ValueError) as e:
            logging.error(f"❌ Ошибка обработки данных WebApp: {e}")
            await message.answer("❌ Ошибка обработки данных WebApp!")
    else:
        logging.warning("❌ WebApp-данные отсутствуют!")
        await message.answer("❌ Данные из WebApp отсутствуют!")

    await state.clear()

async def catch_all_messages(message: types.Message):
    """Логируем все входящие сообщения"""
    logging.info(f"📩 Пришло сообщение: {message.text}")
    if message.web_app_data:
        logging.info(f"📩 Данные WebApp: {message.web_app_data.data}")
    else:
        logging.info("❌ WebApp-данные отсутствуют в сообщении!")

def register_user_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
    dp.message.register(set_cuisine, UserSurvey.cuisine)
    dp.message.register(set_avg_receipt, UserSurvey.avg_receipt)
    dp.message.register(set_food_preferences, UserSurvey.food_preferences)
    dp.message.register(webapp_data_handler, lambda msg: msg.content_type == ContentType.WEB_APP_DATA)
    dp.message.register(catch_all_messages)

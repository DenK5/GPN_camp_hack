from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from app.core.services.user_service import UserService
from app.presentation.ui.messages import (
    WELCOME_MESSAGE, ASK_CUISINE, ASK_AVG_RECEIPT, ASK_FOOD, ASK_OFFICE_LOCATION
)
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSurvey(StatesGroup):
    cuisine = State()
    avg_receipt = State()
    food_preferences = State()
    office_location = State()


async def start_command(message: types.Message, state: FSMContext):
    """Обработчик команды /start, начало анкеты"""
    await message.answer(WELCOME_MESSAGE)
    await message.answer(ASK_CUISINE)
    await state.set_state(UserSurvey.cuisine)


async def set_cuisine(message: types.Message, state: FSMContext):
    """Устанавливаем предпочтения по кухне (свободный ввод)"""
    await state.update_data(cuisine=message.text)
    await message.answer(ASK_AVG_RECEIPT)
    await state.set_state(UserSurvey.avg_receipt)


async def set_avg_receipt(message: types.Message, state: FSMContext):
    """Устанавливаем комфортный средний чек"""
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи сумму числом.")
        return
    await state.update_data(avg_receipt=int(message.text))
    await message.answer(ASK_FOOD)
    await state.set_state(UserSurvey.food_preferences)


async def set_food_preferences(message: types.Message, state: FSMContext):
    """Устанавливаем предпочтения в еде (любимые, нелюбимые продукты, аллергии)"""
    await state.update_data(food_preferences=message.text)
    
    data = await state.get_data()
    user_service = UserService()
    
    if not data.get("base_position"):
        await message.answer("Пожалуйста, укажи местоположение своего офиса на карте.")
        await message.answer(ASK_OFFICE_LOCATION)

        location_button = KeyboardButton(text="Отправить местоположение", request_location=True)
        
        markup = ReplyKeyboardMarkup(keyboard=[[location_button]], resize_keyboard=True)
        # await message.answer("Пожалуйста, отправь местоположение своего офиса.", reply_markup=markup)

        await state.set_state(UserSurvey.office_location)
        return  

    try:
        await user_service.update_preferences(
            telegram_id=message.from_user.id,
            cuisine=data["cuisine"],
            avg_receipt=data["avg_receipt"],
            food_preferences=data["food_preferences"]
        )
        await message.answer("Спасибо! Теперь я знаю твои предпочтения и смогу подобрать лучшие места для обеда 🍽️")
    except Exception as e:
        logger.error(f"Ошибка при обновлении предпочтений: {e}")
        await message.answer("Произошла ошибка при сохранении данных. Попробуйте позже.")
    
    await state.clear()


async def set_office_location(message: types.Message, state: FSMContext):
    """Сохраняем местоположение офиса"""
    try:
        if message.location:
            latitude = message.location.latitude
            longitude = message.location.longitude

            data = await state.get_data()
            user_service = UserService()
            base_position = f"Latitude: {latitude}, Longitude: {longitude}"

            await user_service.set_base_position(message.from_user.id, base_position)

            await message.answer(f"Ваш офис успешно сохранен: {base_position}")
        else:
            await message.answer("Пожалуйста, отправьте ваше местоположение.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении местоположения: {e}")
        await message.answer("Произошла ошибка при получении местоположения. Попробуйте снова.")
    
    await state.clear()

def register_user_handlers(dp: Dispatcher):
    """Регистрируем обработчики"""
    dp.message.register(start_command, Command("start"))
    dp.message.register(set_cuisine, UserSurvey.cuisine)
    dp.message.register(set_avg_receipt, UserSurvey.avg_receipt)
    dp.message.register(set_food_preferences, UserSurvey.food_preferences)
    dp.message.register(set_office_location, UserSurvey.office_location)

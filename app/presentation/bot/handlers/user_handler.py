from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from app.core.services.user_service import UserService
from app.presentation.ui.messages import (
    WELCOME_MESSAGE, ASK_CUISINE, ASK_AVG_RECEIPT, ASK_FOOD, ASK_OFFICE_LOCATION
)
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
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
    """Сохранение предпочтений в еде"""
    await state.update_data(food_preferences=message.text)
    
    web_app_url = "https://mycustomname.loca.lt"

    web_app = WebAppInfo(url=web_app_url)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Ввести адрес", web_app=web_app)]
    ])

    
    await message.answer("Теперь укажи адрес офиса, где ты работаешь:", reply_markup=keyboard)
    await state.set_state(UserSurvey.office_location)

async def set_office_location(callback_query: types.CallbackQuery, state: FSMContext):
    """Обрабатываем адрес с web-app"""
    try:
        address = callback_query.web_app_data.data  # Получаем адрес из web-app
        data = await state.get_data()
        user_service = UserService()
        
        await user_service.set_base_position(callback_query.from_user.id, address)
        
        await callback_query.message.answer(f"Ваш офис успешно сохранен: {address}")
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Ошибка при сохранении адреса: {e}")
        await callback_query.message.answer("Произошла ошибка, попробуйте снова.")
    
    await state.clear()

def register_user_handlers(dp: Dispatcher):
    """Регистрируем обработчики"""
    dp.message.register(start_command, Command("start"))
    dp.message.register(set_cuisine, UserSurvey.cuisine)
    dp.message.register(set_avg_receipt, UserSurvey.avg_receipt)
    dp.message.register(set_food_preferences, UserSurvey.food_preferences)
    dp.callback_query.register(set_office_location)


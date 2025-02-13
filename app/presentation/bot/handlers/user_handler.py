from aiogram import types, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from app.core.services.user_service import UserService
from app.presentation.ui.messages import WELCOME_MESSAGE, ASK_CUISINE, ASK_AVG_RECEIPT, ASK_FOOD

class UserSurvey(StatesGroup):
    cuisine = State()
    avg_receipt = State()
    food_preferences = State()

async def start_command(message: types.Message, state: FSMContext):
    """ Обработчик команды /start, начало анкеты """
    await message.answer(WELCOME_MESSAGE)
    await message.answer(ASK_CUISINE)
    await state.set_state(UserSurvey.cuisine)

async def set_cuisine(message: types.Message, state: FSMContext):
    """ Устанавливаем предпочтения по кухне (свободный ввод) """
    await state.update_data(cuisine=message.text)
    await message.answer(ASK_AVG_RECEIPT)
    await state.set_state(UserSurvey.avg_receipt)

async def set_avg_receipt(message: types.Message, state: FSMContext):
    """ Устанавливаем комфортный средний чек """
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введи сумму числом.")
        return
    await state.update_data(avg_receipt=int(message.text))
    await message.answer(ASK_FOOD)
    await state.set_state(UserSurvey.food_preferences)

async def set_food_preferences(message: types.Message, state: FSMContext):
    """ Устанавливаем предпочтения в еде (любимые, нелюбимые продукты, аллергии) """
    await state.update_data(food_preferences=message.text)
    
    data = await state.get_data()
    user_service = UserService()
    user_service.update_preferences(
        telegram_id=message.from_user.id,
        cuisine=data["cuisine"],
        avg_receipt=data["avg_receipt"],
        food_preferences=data["food_preferences"]
    )

    await message.answer("Спасибо! Теперь я знаю твои предпочтения и смогу подобрать лучшие места для обеда 🍽️")
    await state.clear()

def register_user_handlers(dp: Dispatcher):
    """ Регистрируем обработчики """
    dp.message.register(start_command, commands="start")
    dp.message.register(set_cuisine, state=UserSurvey.cuisine)
    dp.message.register(set_avg_receipt, state=UserSurvey.avg_receipt)
    dp.message.register(set_food_preferences, state=UserSurvey.food_preferences)

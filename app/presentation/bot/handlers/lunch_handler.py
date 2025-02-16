from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


class LunchSurvey(StatesGroup):
    choose_method = State()

async def start_lunch_command(message: types.Message, state: FSMContext):
    """Обрабатывает команду /lunch и предлагает пользователю выбрать способ выбора места обеда."""
    logging.info("✅ Обработчик /lunch вызван!")
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]
        ],
        resize_keyboard=True
    )
    await message.answer("Вы хотите выбрать место обеда самостоятельно?", reply_markup=keyboard)
    await state.set_state(LunchSurvey.choose_method)


async def process_lunch_choice(message: types.Message, state: FSMContext):
    """Обрабатывает ответ пользователя на вопрос о выборе способа поиска места обеда."""
    logging.info(f"📩 Пользователь выбрал: {message.text}")

    choice = message.text.strip().lower()
    if choice == "✅ да":
        await message.answer("Вы можете выбрать место обеда самостоятельно через нашу карту.", reply_markup=ReplyKeyboardRemove())
    elif choice == "❌ нет":
        await message.answer("Мы подберем вам лучшее место для обеда!", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")
        return
    
    await state.clear()
    
def register_lunch_handlers(dp: Dispatcher):
    logging.info("🛠️ Регистрируем обработчики для /lunch...")
    dp.message.register(start_lunch_command, Command("lunch"))
    dp.message.register(process_lunch_choice, LunchSurvey.choose_method)
    logging.info("✅ Обработчики для /lunch зарегистрированы!")

import logging
from aiogram import types, Dispatcher, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime, timezone, timedelta

class LunchSurvey(StatesGroup):
    choose_method = State()
    choose_date_and_time = State()
    choose_end_time = State()

async def start_lunch_command(message: types.Message, bot: Bot):
    """Обрабатывает команду /lunch в групповом чате, отправляя кнопку 'Пойдем на обед'."""
    if message.chat.type == "private":
        await start_lunch_private(message)
        return

    chat_id = message.chat.id
    members = await bot.get_chat_administrators(chat_id)
    user_ids = [member.user.id for member in members if not member.user.is_bot]
    logging.info(f"📋 id чата: {chat_id}")
    logging.info(f"📋 Собран список участников: {user_ids}")

    bot_info = await bot.get_me()

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text="Пойдем на обед",
            url=f"https://t.me/{bot_info.username}?start=lunch"
        )]]
    )

    await message.answer("🍽 Кто хочет пойти на обед? Жмите кнопку!", reply_markup=inline_keyboard)


async def start_lunch_private(message: types.Message, state: FSMContext):
    """Обрабатывает команду /lunch в личных сообщениях."""
    logging.info(f"👤 Пользователь {message.from_user.id} перешел в ЛС")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]],
        resize_keyboard=True
    )

    await message.answer("Вы хотите выбрать место обеда самостоятельно?", reply_markup=keyboard)
    await state.set_state(LunchSurvey.choose_method)


async def process_lunch_choice(message: types.Message, state: FSMContext):
    """Обрабатывает выбор пользователя (самостоятельно или автоматически)."""
    logging.info(f"📩 Пользователь выбрал: {message.text}")

    choice = message.text.strip().lower()
    if choice == "✅ да":
        calendar = SimpleCalendar(locale='ru_RU')
        await message.answer("Выберите дату обеда:", reply_markup=await calendar.start_calendar())
        await state.set_state(LunchSurvey.choose_date_and_time)
    elif choice == "❌ нет":
        await message.answer("Мы подберем вам лучшее место!", reply_markup=ReplyKeyboardRemove())
        await state.clear()
    else:
        await message.answer("Выберите один из предложенных вариантов.")


async def process_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """Обрабатывает выбор даты пользователем."""
    logging.info(f"callback_query.data: {callback_query.data}")

    try:
        calendar = SimpleCalendar(locale='ru_RU')
        selected, date = await calendar.process_selection(callback_query, callback_data)

        if selected:
            formatted_date = date.strftime("%d.%m.%Y")
            await state.update_data(lunch_date=formatted_date)

            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(
                    text="Ввести время", 
                    web_app=types.WebAppInfo(url="https://expented.github.io/tgdtp/?hide=date&zoom=2")
                )]],
                resize_keyboard=True
            )
            await callback_query.message.answer(
                f"Вы выбрали дату обеда: {formatted_date}. Теперь введите время обеда:",
                reply_markup=keyboard
            )
            await state.set_state(LunchSurvey.choose_date_and_time)

        else:
            await callback_query.answer("Ошибка при выборе даты. Попробуйте снова.")
    except Exception as e:
        logging.error(f"Ошибка в обработке календаря: {e}")
        await callback_query.message.answer("Произошла ошибка при обработке календаря. Пожалуйста, попробуйте снова.")


async def process_web_app_time(message: types.Message, state: FSMContext):
    """Обрабатывает полученное значение времени из WebApp."""
    try:
        logging.info(f"Получено сообщение от пользователя {message.from_user.id}: {message.web_app_data}")

        if not message.web_app_data or not message.web_app_data.data:
            logging.error("❌ Время не было передано. Пожалуйста, попробуйте снова.")
            await message.answer("❌ Время не было передано. Пожалуйста, попробуйте снова.")
            return

        data = message.web_app_data.data.split("_")
        if len(data) != 2:
            logging.error("❌ Неверный формат данных. Пожалуйста, попробуйте снова.")
            await message.answer("❌ Неверный формат данных. Пожалуйста, попробуйте снова.")
            return

        timestamp = int(data[0])
        timezone_offset = int(data[1])

        utc_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        local_time = utc_time + timedelta(minutes=timezone_offset)

        adjusted_time = local_time - timedelta(hours=12)

        formatted_time = adjusted_time.strftime("%H:%M")
        logging.info(f"⏰ Время обеда (после корректировки): {formatted_time}")

        await state.update_data(lunch_time=formatted_time)

        user_data = await state.get_data()
        lunch_date = user_data.get("lunch_date")

        if lunch_date:
            await message.answer(f"Теперь введите время окончания опроса (ЧЧ:ММ, например 12:30):")
            await state.set_state(LunchSurvey.choose_end_time)

        else:
            await message.answer("Не удалось получить дату обеда. Попробуйте снова.")
    except Exception as e:
        logging.error(f"Ошибка при обработке времени: {e}")
        await message.answer("❌ Произошла ошибка при обработке времени. Пожалуйста, попробуйте снова.")



async def process_poll_end_time(message: types.Message, state: FSMContext):
    """Обрабатывает ввод времени окончания опроса."""

    poll_end_time_data = message.text.strip() if message.text else message.web_app_data.data
    logging.info(f"Получено время: {poll_end_time_data}")
    
    if not poll_end_time_data:
        await message.answer("❌ Время не было передано. Пожалуйста, попробуйте снова.")
        return
    
    try:
        timestamp, timezone_offset = poll_end_time_data.split("_")
        timestamp = int(timestamp)
        timezone_offset = int(timezone_offset)
    except ValueError:
        await message.answer("❌ Неверный формат данных. Пожалуйста, попробуйте снова.")
        return
    
    utc_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
    local_time = utc_time + timedelta(minutes=timezone_offset)

    adjusted_time = local_time - timedelta(hours=12)

    formatted_time = adjusted_time.strftime("%H:%M")
    logging.info(f"⏰ Время окончания опроса: {formatted_time}")

    user_data = await state.get_data()
    lunch_time = user_data.get("lunch_time")

    if formatted_time >= lunch_time:
        await message.answer("Время окончания опроса должно быть раньше времени обеда! Попробуйте снова.")
        return

    await message.answer(f"📅 Опрос завершится в {formatted_time}, обед в {lunch_time}.")
    await state.clear()

def register_lunch_handlers(dp: Dispatcher, bot: Bot):
    logging.info("🛠️ Регистрируем обработчики для /lunch...")
    dp.message.register(start_lunch_command, Command("lunch"))
    dp.message.register(process_lunch_choice, LunchSurvey.choose_method)
    dp.callback_query.register(process_calendar, SimpleCalendarCallback.filter())
    dp.message.register(process_web_app_time, LunchSurvey.choose_date_and_time)
    dp.message.register(process_poll_end_time, LunchSurvey.choose_end_time)
    logging.info("✅ Обработчики для /lunch зарегистрированы!")

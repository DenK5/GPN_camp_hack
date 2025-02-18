import logging
from aiogram import types, Dispatcher, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from datetime import datetime, timezone, timedelta
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from app.infrastructure.external.map_api.models.Point import Point
from app.application.use_cases.create_poll_use_case import CreatePollUseCase
from app.core.services.poll_service import PollService
from aiogram.types import Message
import json
import asyncio

logging.basicConfig(level=logging.INFO)

class LunchSurvey(StatesGroup):
    choose_method = State()
    choose_date_and_time = State()
    choose_end_time = State()
    choose_location = State()
    location_name = State()
    chat_id = State()
    members = State()

async def start_lunch_command(message: types.Message, bot: Bot, state: FSMContext):
    """Обрабатывает команду /lunch только в групповом чате."""
    if message.chat.type != "supergroup" and message.chat.type != "group":
        await message.answer("Эта команда доступна только в групповых чатах.")
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
            url=f"https://t.me/{bot_info.username}?start=lunch_{chat_id}"
        )]]
    )

    await message.answer("🍽 Кто хочет пойти на обед? Жмите кнопку!", reply_markup=inline_keyboard)

    await state.update_data(chat_id=chat_id, members=user_ids)

async def start_lunch_private(message: types.Message, state: FSMContext):
    """Запускает процесс выбора обеда в ЛС."""
    logging.info(f"👤 Пользователь {message.from_user.id} перешел в ЛС")
    
    data = await state.get_data()
    logging.info(f"✅ Данные в состоянии после сохранения chat_id: {data}")

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

            logging.info(f"📅 Дата обеда сохранена: {formatted_date}")

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
            await message.answer("❌ Время не было передано. Попробуйте снова.")
            return

        data = message.web_app_data.data.split("_")
        if len(data) != 2:
            await message.answer("❌ Неверный формат данных. Попробуйте снова.")
            return

        timestamp = int(data[0])
        timezone_offset = int(data[1])

        utc_time = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc)
        local_time = utc_time + timedelta(minutes=timezone_offset)
        djusted_time = local_time - timedelta(hours=12)
        formatted_time = djusted_time.strftime("%H:%M")
        logging.info(f"⏰ Время обеда сохранено: {formatted_time}")

        await state.update_data(lunch_time=formatted_time)

        user_data = await state.get_data()
        lunch_date = user_data.get("lunch_date")

        if lunch_date:
            choose_date_and_time = f"{lunch_date} {formatted_time}"
            await state.update_data(choose_date_and_time=choose_date_and_time)
            await message.answer(f"📅 Вы выбрали обед: {choose_date_and_time}\n\nТеперь введите время окончания опроса (ЧЧ:ММ, например 12:30):")
            await state.set_state(LunchSurvey.choose_end_time)
        else:
            await message.answer("❌ Ошибка: Не удалось получить дату обеда. Попробуйте снова.")

    except Exception as e:
        logging.error(f"Ошибка при обработке времени: {e}")
        await message.answer("❌ Произошла ошибка при обработке времени. Попробуйте снова.")


async def process_poll_end_time(message: types.Message, state: FSMContext):
    """Обрабатывает ввод времени окончания опроса и предлагает выбрать место на карте."""
    
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

    await state.update_data(choose_end_time=formatted_time)

    await message.answer(f"📅 Опрос завершится в {formatted_time}, обед в {lunch_time}.")

    web_app_url = "https://b34cac08-647f-4fc5-b111-a7174ebcf812.tunnel4.com"
    web_app = types.WebAppInfo(url=web_app_url)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Ввести адрес", web_app=web_app)]],
        resize_keyboard=True
    )

    await message.answer("Теперь выберите место обеда на карте:", reply_markup=keyboard)
    await state.set_state(LunchSurvey.choose_location)


async def process_web_app_location(message: types.Message, state: FSMContext):
    """Обрабатывает ввод координат из WebApp и запрашивает название заведения."""
    if message.web_app_data:
        try:
            data = json.loads(message.web_app_data.data)
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            address = data.get("address")

            if latitude and longitude:
                latitude, longitude = float(latitude), float(longitude)
                location = {"latitude": latitude, "longitude": longitude}
                await state.update_data(choose_location=location)
            elif address:
                await state.update_data(choose_location=address)
            else:
                raise ValueError("Данные не содержат адреса или координат")

            logging.info(f"📍 Выбранные координаты: lat={latitude}, lon={longitude}")
                    
            await message.answer(
                f"📍 Вы выбрали место:\n"
                f"🌍 Широта: {latitude}\n"
                f"🌏 Долгота: {longitude}\n"
                f"Уточните название заведения:"
            )

            await state.set_state(LunchSurvey.location_name)

        except Exception as e:
            logging.error(f"❌ Общая ошибка при обработке координат: {e}")
            await message.answer("❌ Произошла ошибка при обработке координат. Попробуйте снова.")

async def track_poll_end_time(chat_id: int, poll_message_id: int, end_time: str, choose_date_and_time: str, bot: Bot):
    """Фоновая задача для отслеживания времени окончания опроса."""
    
    if not choose_date_and_time:
        logging.error("❌ Ошибка: choose_date_and_time отсутствует!")
        return

    try:
        choose_dt = datetime.strptime(choose_date_and_time, "%d.%m.%Y %H:%M")
        end_hours, end_minutes = map(int, end_time.split(":"))
        end_dt = choose_dt.replace(hour=end_hours, minute=end_minutes)

        now = datetime.now()
        while now < end_dt:
            await asyncio.sleep(30)
            now = datetime.now()

        poll_results = await bot.stop_poll(chat_id, poll_message_id)
        results_message = "📊 *Результаты голосования:*\n"

        for option in poll_results.options:
            results_message += f"✅ {option.text}: {option.voter_count} голосов\n"


        await bot.send_message(chat_id, results_message, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"❌ Ошибка в track_poll_end_time: {e}")



async def process_location_name(message: types.Message, state: FSMContext, bot: Bot):
    """Обрабатывает ввод названия заведения и завершает опрос."""
    location_name = message.text.strip()
    logging.info(f"Введено имя {location_name}")
    
    if not location_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз.")
        return

    user_data = await state.get_data()
    date_and_time = user_data.get("choose_date_and_time")
    end_time = user_data.get("choose_end_time")
    location = user_data.get("choose_location")
    chat_id = user_data.get("chat_id")

    if not chat_id:
        logging.error("❌ Ошибка: chat_id отсутствует в состоянии!")
        await message.answer("❌ Не удалось получить chat_id. Попробуйте снова.")
        return

    if not location:
        logging.error("❌ Ошибка: координаты отсутствуют в state!")
        await message.answer("❌ Ошибка: координаты не выбраны. Пожалуйста, выберите место еще раз.")
        return

    await state.update_data(location_name=location_name)
    
    poll_service = PollService()
    create_poll_use_case = CreatePollUseCase(poll_service)
    poll_message = await create_poll_use_case.execute(chat_id, location_name, end_time)
    
    logging.info(f"Тип poll_message: {type(poll_message)}, содержимое: {poll_message}")
    
    poll_message_id = poll_message.get("message_id")
    if not poll_message_id:
        logging.error("❌ Ошибка: 'message_id' отсутствует в poll_message!")
        await message.answer("❌ Ошибка при создании опроса. Попробуйте снова.")
        return

    asyncio.create_task(track_poll_end_time(chat_id, poll_message_id, end_time, date_and_time, bot))
    logging.info(f"✅ Опрос по {location_name} отправлен в групповой чат {chat_id}")
    await state.clear()


def register_lunch_handlers(dp: Dispatcher, bot: Bot):
    logging.info("🛠️ Регистрируем обработчики для /lunch...")

    dp.message.register(start_lunch_command, Command("lunch"))
    dp.message.register(process_lunch_choice, LunchSurvey.choose_method)
    dp.callback_query.register(process_calendar, SimpleCalendarCallback.filter())
    dp.message.register(process_web_app_time, LunchSurvey.choose_date_and_time)
    dp.message.register(process_poll_end_time, LunchSurvey.choose_end_time)
    dp.message.register(process_web_app_location, LunchSurvey.choose_location)
    dp.message.register(process_location_name, LunchSurvey.location_name)

    logging.info("✅ Обработчики для /lunch зарегистрированы!")

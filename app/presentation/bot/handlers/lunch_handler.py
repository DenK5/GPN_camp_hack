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
from app.core.services.user_service import UserService
from app.core.entities.user import User
import json
import asyncio
from app.core.services.ranking_service import RankingService

# Инициализация объекта RankingService
ranking_service = RankingService()


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
            url=f"https://t.me/{bot_info.username}?start=lunch_{chat_id}_{','.join(map(str, user_ids))}"
        )]]
    )

    await message.answer("🍽 Кто хочет пойти на обед? Жмите кнопку!", reply_markup=inline_keyboard)

    # Сохраняем chat_id и список участников отдельно
    await state.update_data(chat_id=chat_id, members=user_ids)



async def start_lunch_private(message: types.Message, state: FSMContext):
    """Запускает процесс выбора обеда в ЛС."""
    logging.info(f"👤 Пользователь {message.from_user.id} перешел в ЛС")

    # Получаем данные из состояния
    data = await state.get_data()
    logging.info(f"✅ Данные в состоянии после сохранения chat_id: {data}")

    # Разбираем chat_id на части (первая часть — chat_id, остальные — members)
    chat_id = data.get("chat_id")
    if chat_id:
        chat_id_parts = chat_id.split('_')
        group_chat_id = chat_id_parts[0]  # id группы
        members = chat_id_parts[1:]  # все остальные части - это члены группы
        logging.info(f"📋 Извлеченные данные: group_chat_id={group_chat_id}, members={members}")
    else:
        logging.error("chat_id отсутствует в состоянии.")
        await message.answer("chat_id не найден.")
        return

    # Сохраняем group_chat_id и members в состояние
    await state.update_data(chat_id=group_chat_id, members=members)
    logging.info(f"📋 Состояние обновлено: group_chat_id={group_chat_id}, members={members}")

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

    state_data = await state.get_data()
    chat_id = state_data.get("chat_id")
    members = state_data.get("members")


    if chat_id:
        chat_id_parts = chat_id.split('_')
        if len(chat_id_parts) == 2:
            
            chat_id = chat_id_parts[0]
            user_id = chat_id_parts[1]
            logging.info(f"📩 Пользователь выбрал: {user_id}")
    else:
        chat_id = None
        user_id = None

    if not members:
        await message.answer("Ошибка: не удалось получить список участников. Попробуйте еще раз.")
        return

    if choice == "✅ да":
        calendar = SimpleCalendar(locale='ru_RU')
        await message.answer("Выберите дату обеда:", reply_markup=await calendar.start_calendar())
        await state.set_state(LunchSurvey.choose_date_and_time)

    elif choice == "❌ нет":
        telegram_id = message.from_user.id
        async with UserService() as user_service:
            users = []
            
            for member_id in members:
                user_data = await user_service.get_user_data(member_id)
                if user_data:
                    users.append(User(
                        telegram_id=member_id,
                        chat_id=str(member_id),
                        base_position_lat = user_data['base_position_lat'],
                        base_position_lng = user_data['base_position_lng'],
                        avg_receipt = user_data['avg_receipt'],
                        preferences_by_type=user_data['preferences_by_type'],
                        preferences_by_food=user_data['preferences_by_food']
                        
                    ))

            current_user_data = await user_service.get_user_data(telegram_id)
            if current_user_data:
                users.append(User(
                    telegram_id=telegram_id,
                    chat_id=str(telegram_id),
                    base_position_lat = user_data['base_position_lat'],
                    base_position_lng = user_data['base_position_lng'],
                    avg_receipt = user_data['avg_receipt'],
                    preferences_by_type=current_user_data['preferences_by_type'],
                    preferences_by_food=current_user_data['preferences_by_food']
                ))

            top_5_places = await ranking_service.get_variants(users[0], users[1:])

            if top_5_places:
                response_message = "Вот 5 лучших мест для обеда:\n\n"
                for i, place in enumerate(top_5_places, 1):
                    response_message += f"{i}. {place.place_name}\n"

                await message.answer(response_message)

        await message.answer("Выбор завершен.", reply_markup=ReplyKeyboardRemove())

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

    web_app_url = "https://b93f303f-f4ba-4a35-9588-e7db2e5dca60.tunnel4.com"
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

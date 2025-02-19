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
from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
import json
import asyncio
from app.core.services.ranking_service import RankingService
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from config import Config


ranking_service = RankingService()


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

    bot_info = await bot.get_me()

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(
            text="Пойдем на обед",
            url=f"https://t.me/{bot_info.username}?start=lunch_{chat_id}_{','.join(map(str, user_ids))}"
        )]]
    )

    await message.answer("🍽 Кто хочет пойти на обед? Нужно уточнить пару деталей!", reply_markup=inline_keyboard)

    await state.update_data(chat_id=chat_id, members=user_ids)


async def start_lunch_private(message: types.Message, state: FSMContext):
    """Запускает процесс выбора обеда в ЛС."""

    data = await state.get_data()

    chat_id = data.get("chat_id")
    if chat_id:
        chat_id_parts = chat_id.split('_')
        group_chat_id = chat_id_parts[0]
        members = chat_id_parts[1:]
    else:
        await message.answer("chat_id не найден.")
        return

    await state.update_data(chat_id=group_chat_id, members=members)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]],
        resize_keyboard=True
    )

    await message.answer("Вы хотите выбрать место обеда самостоятельно? Если выберете варинт НЕТ, то за вс это сделает бот", reply_markup=keyboard)
    await state.set_state(LunchSurvey.choose_method)


async def process_lunch_choice(message: types.Message, state: FSMContext, bot: Bot):
    """Обрабатывает выбор пользователя (самостоятельно или автоматически)."""

    choice = message.text.strip().lower()
    state_data = await state.get_data()
    members = state_data.get("members")
    chat_id = state_data.get("chat_id")

    if not members or not chat_id:
        await message.answer("Ошибка: не удалось получить данные. Попробуйте еще раз.")
        return

    if choice == "✅ да" or choice == "❌ нет":
        await state.update_data(lunch_method_choice=choice)

        calendar = SimpleCalendar(locale='ru_RU')
        await message.answer("Выберите дату обеда:", reply_markup=await calendar.start_calendar())
        await state.set_state(LunchSurvey.choose_date_and_time)
    else:
        await message.answer("Выберите один из предложенных вариантов.")


async def process_calendar(callback_query: types.CallbackQuery, callback_data: dict, state: FSMContext):
    """Обрабатывает выбор даты пользователем."""

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
        await message.answer("❌ Произошла ошибка при обработке времени. Попробуйте снова.")


async def process_poll_end_time(message: types.Message, state: FSMContext, bot: Bot ):
    """Обрабатывает ввод времени окончания опроса и предлагает выбрать место на карте."""
    
    poll_end_time_data = message.text.strip() if message.text else message.web_app_data.data
    
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

    user_data = await state.get_data()
    lunch_time = user_data.get("lunch_time")

    if formatted_time >= lunch_time:
        await message.answer("Время окончания опроса должно быть раньше времени обеда! Попробуйте снова.")
        return

    await state.update_data(choose_end_time=formatted_time)

    await message.answer(f"📅 Опрос завершится в {formatted_time}, обед в {lunch_time}.")
    
    lunch_method_choice = user_data.get("lunch_method_choice")
    
    if lunch_method_choice == "✅ да":
        web_app_url = "https://d83bc93f-60f3-4028-bdb7-469f4f8ffe99.tunnel4.com"
        web_app = types.WebAppInfo(url=web_app_url)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Ввести адрес", web_app=web_app)]],
            resize_keyboard=True
        )

        await message.answer("Теперь выберите место обеда на карте:", reply_markup=keyboard)
        await state.set_state(LunchSurvey.choose_location)
    else:
        user_data = await state.get_data()
        chat_id = user_data.get("chat_id")
        members = user_data.get("members")
        lunch_date_time = user_data.get("choose_date_and_time")
        end_time = user_data.get("choose_end_time")
        lunch_method_choice = user_data.get("lunch_method_choice")

        telegram_id = message.from_user.id
        async with UserService() as user_service:
            users = [await user_service.get_user_data(member_id) for member_id in members]
            users = [User(**user) for user in users if user]

            current_user_data = await user_service.get_user_data(telegram_id)
            if current_user_data:
                users.append(User(**current_user_data))
                
        top_5_places = [ 
            PlaceInfo(
                id='70000001069595862',
                address_name='Маяковского, 39',
                name='У Ларисы, кафе-бар',
                point=Point(lat=59.942208, lon=30.355653),
                reviews={'general_rating': 4.5},
                rubrics=['Кафе', 'Бары', 'Доставка еды', 'Рюмочные'],
                avg_lunch_cost=-1,
                avg_business_lunch_cost=-1,
                cuisines=['Узбекская кухня']
            ),
            PlaceInfo(
                id='5348553838529810',
                address_name='Радищева, 36',
                name='Траппист, бельгийская брассерия',
                point=Point(lat=59.94156, lon=30.363407),
                reviews={'general_rating': 4.6},
                rubrics=['Рестораны', 'Бары', 'Доставка еды'],
                avg_lunch_cost=2000,
                avg_business_lunch_cost=990,
                cuisines=['Французская кухня']
            ),
            PlaceInfo(
                id='70000001093839054',
                address_name='Восстания, 55',
                name='Мама Тата, грузинская неорюмочная',
                point=Point(lat=59.943178, lon=30.360953),
                reviews={'general_rating': 4.8},
                rubrics=['Кафе', 'Рюмочные', 'Бары'],
                avg_lunch_cost=850,
                avg_business_lunch_cost=350,
                cuisines=['Грузинская кухня', 'Кавказская кухня', 'Европейская кухня']
            ),
            PlaceInfo(
                id='70000001060749771',
                address_name='Невский проспект, 128',
                name='Малатан, китайский и паназиатский ресторан',
                point=Point(lat=59.931345, lon=30.366953),
                reviews={'general_rating': 4.9},
                rubrics=['Кафе', 'Доставка еды'],
                avg_lunch_cost=550,
                avg_business_lunch_cost=337,
                cuisines=['Азиатская кухня']
            ),
            PlaceInfo(
                id='70000001046974460',
                address_name='улица Некрасова, 21',
                name='Ossu, лапшичная',
                point=Point(lat=59.938676, lon=30.358366),
                reviews={'general_rating': 4.7},
                rubrics=['Кафе', 'Доставка еды'],
                avg_lunch_cost=1300,
                avg_business_lunch_cost=450,
                cuisines=['Паназиатская кухня']
            )
        ]

        if not top_5_places:
            await message.answer("❌ Не удалось найти подходящие места.")
            return

        detailed_info_message = "Вот 5 лучших мест для обеда:\n\n"
        for place in top_5_places:
            detailed_info_message += f"🍽️ {place.place_name}\n"
            detailed_info_message += f"📍 Адрес: {place.address_name}\n"
            detailed_info_message += f"⭐ Рейтинг: {place.general_rating} (из 5)\n"
            
            if place.avg_lunch_cost > 0:
                detailed_info_message += f"💵 Средний обед: {place.avg_lunch_cost} ₽\n"
            
            if place.avg_business_lunch_cost > 0:
                detailed_info_message += f"💼 Средний бизнес-ланч: {place.avg_business_lunch_cost} ₽\n"
            
            if place.cuisines:
                if isinstance(place.cuisines, list):
                    detailed_info_message += f"🍴 Кухни: {', '.join(place.cuisines)}\n"
                else:
                    detailed_info_message += f"🍴 Кухня: {place.cuisines}\n"

            detailed_info_message += "\n"

        await bot.send_message(chat_id, detailed_info_message)

        poll_options = [place.place_name for place in top_5_places]
        poll_message = await bot.send_poll(
            chat_id, "Где обедаем?", poll_options, is_anonymous=False
        )
        asyncio.create_task(track_poll_end_time(chat_id, poll_message.message_id, end_time, lunch_date_time, bot))

        await state.clear()


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
                f"Уточните название заведения:"
            )

            await state.set_state(LunchSurvey.location_name)

        except Exception as e:
            await message.answer("❌ Произошла ошибка при обработке координат. Попробуйте снова.")

async def track_poll_end_time(chat_id: int, poll_message_id: int, end_time: str, choose_date_and_time: str, bot: Bot):
    """Фоновая задача для отслеживания времени окончания опроса."""
    
    if not choose_date_and_time:
        return

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


async def process_location_name(message: types.Message, state: FSMContext, bot: Bot):
    """Обрабатывает ввод названия заведения и завершает опрос."""
    location_name = message.text.strip()
    
    if not location_name:
        await message.answer("❌ Название не может быть пустым. Попробуйте еще раз.")
        return

    user_data = await state.get_data()
    date_and_time = user_data.get("choose_date_and_time")
    dt = datetime.strptime(date_and_time, "%d.%m.%Y %H:%M")
    time_str = dt.strftime("%H:%M")
    end_time = user_data.get("choose_end_time")
    location = user_data.get("choose_location")
    chat_id = user_data.get("chat_id")

    if not chat_id:
        await message.answer("❌ Не удалось получить chat_id. Попробуйте снова.")
        return

    if not location:
        await message.answer("❌ Ошибка: координаты не выбраны. Пожалуйста, выберите место еще раз.")
        return

    await state.update_data(location_name=location_name)
    
    detailed_info_message = f"Вас преглашают пообедать в этом местечке:\n\n"
    map = Map2GisAPI(Config.MAP_API_KEY)
    city = map.get_city_by_point(Point(lat=location['latitude'], lon=location['longitude']))
    adress = await map.get_address_by_coords(location['latitude'], location['longitude'])
    place = await map.get_place_info(city, adress)
    detailed_info_message += f"🍽️ {place.place_name}\n"
    detailed_info_message += f"📍 Адрес: {place.address_name}\n"
    detailed_info_message += f"⭐ Рейтинг: {place.general_rating} (из 5)\n"
    
    if place.avg_lunch_cost > 0:
        detailed_info_message += f"💵 Средний обед: {place.avg_lunch_cost} ₽\n"
    
    if place.avg_business_lunch_cost > 0:
        detailed_info_message += f"💼 Средний бизнес-ланч: {place.avg_business_lunch_cost} ₽\n"
    
    if place.cuisines:
        if isinstance(place.cuisines, list):
            detailed_info_message += f"🍴 Кухни: {', '.join(place.cuisines)}\n"
        else:
            detailed_info_message += f"🍴 Кухня: {place.cuisines}\n"

    detailed_info_message += "\n"

    await bot.send_message(chat_id, detailed_info_message)
        
    poll_service = PollService()
    create_poll_use_case = CreatePollUseCase(poll_service)
    poll_message = await create_poll_use_case.execute(chat_id, time_str, location_name, end_time)
    
    
    poll_message_id = poll_message.get("message_id")
    if not poll_message_id:
        await message.answer("❌ Ошибка при создании опроса. Попробуйте снова.")
        return

    asyncio.create_task(track_poll_end_time(chat_id, poll_message_id, end_time, date_and_time, bot))
    await state.clear()


def register_lunch_handlers(dp: Dispatcher, bot: Bot):
    dp.message.register(start_lunch_command, Command("lunch"))
    dp.message.register(process_lunch_choice, LunchSurvey.choose_method)
    dp.callback_query.register(process_calendar, SimpleCalendarCallback.filter())
    dp.message.register(process_web_app_time, LunchSurvey.choose_date_and_time)
    dp.message.register(process_poll_end_time, LunchSurvey.choose_end_time)
    dp.message.register(process_web_app_location, LunchSurvey.choose_location)
    dp.message.register(process_location_name, LunchSurvey.location_name)

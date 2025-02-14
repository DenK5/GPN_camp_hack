from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Location
from config import Config
from app.application.use_cases.location_use_case import LocationUseCase
from app.core.services.location_service import LocationService
from app.infrastructure.external.maps_api import MapsAPIClient

router = Router()
bot = Bot(token=Config.BOT_TOKEN)

class LunchLocation(StatesGroup):
    waiting_for_location = State()  
    waiting_for_address = State()  

maps_api_client = MapsAPIClient()
location_use_case = LocationUseCase(maps_api_client=maps_api_client)
location_service = LocationService(bot=bot)  

@router.message(Command("location"))
async def cmd_location(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду /location.
    """
    await message.answer(
        "Пожалуйста, отправьте геопозицию или введите адрес:"
    )
    await state.set_state(LunchLocation.waiting_for_location)

@router.message(LunchLocation.waiting_for_location, F.location)
async def process_location(message: types.Message, state: FSMContext):
    """
    Обрабатывает полученную геопозицию от пользователя.
    """
    location = message.location
    latitude = location.latitude
    longitude = location.longitude
    await state.update_data(latitude=latitude, longitude=longitude)
    await location_service.send_location(message.chat.id, latitude, longitude)
    await state.clear()  

@router.message(LunchLocation.waiting_for_location, F.text)
async def process_address(message: types.Message, state: FSMContext):
    """
    Обрабатывает текстовое сообщение с адресом от пользователя.

    """
    address = message.text

    location_data = await location_use_case.get_location_by_address(address)

    if location_data:
        latitude = location_data["latitude"]
        longitude = location_data["longitude"]
        await state.update_data(latitude=latitude, longitude=longitude)
        await location_service.send_location(message.chat.id, latitude, longitude)
        await state.clear() 
    else:
        await message.answer("Не удалось распознать адрес. Пожалуйста, попробуйте еще раз.")
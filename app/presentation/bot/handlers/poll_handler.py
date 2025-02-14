from aiogram import types, Dispatcher
from aiogram.filters import Command
from app.application.use_cases.create_poll_use_case import CreatePollUseCase
from app.core.services.poll_service import PollService
from app.presentation.ui.messages import POLL_MESSAGE_TEMPLATE

async def cmd_lunch(message: types.Message, poll_service: PollService):
    location = "Текущая локация пользователя"
    poll = poll_service.create_poll(location)
    await message.answer(POLL_MESSAGE_TEMPLATE.format(options='\n'.join(poll.options)))

def register_handlers_poll(dp: Dispatcher, poll_service: PollService):
    dp.message.register(cmd_lunch, Command("lunch"))

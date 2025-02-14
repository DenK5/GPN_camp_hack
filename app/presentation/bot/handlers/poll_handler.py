from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
import asyncio
from app.application.use_cases.create_poll_use_case import CreatePollUseCase

class PollStates(StatesGroup):
    waiting_for_place = State()
    waiting_for_time = State()
    waiting_for_comment = State()
    waiting_for_poll_end_time = State()

router = Router()
create_poll_use_case = CreatePollUseCase()

polls = {}


@router.message(Command("lunch"))
async def cmd_lunch(message: types.Message):
    """
    Обработчик команды /lunch. Создает первый опрос.
    """
    poll = await create_poll_use_case.execute(
        question="Выбрать место самому?",
        options=["Да", "Нет"],
        duration_minutes=10, 
    )
    poll_message = await message.answer_poll(
        question=poll.question,
        options=poll.options,
        is_anonymous=False,
    )
    await create_poll_use_case.save_poll(poll_message.poll.id, poll)


@router.poll_answer()
async def handle_poll_answer(poll_answer: types.PollAnswer, state: FSMContext):
    """
    Обработчик ответа на опрос.
    """
    poll_id = poll_answer.poll_id
    poll = await create_poll_use_case.get_poll(poll_id)

    if poll and poll.question == "Выбрать место самому?":
        user_answer = poll_answer.option_ids[0]  

        if user_answer == 0:  # Если пользователь выбрал "Да"
            await state.set_state(PollStates.waiting_for_place)
            await poll_answer.bot.send_message(
                chat_id=poll_answer.user.id,
                text="Введите название заведения:",
            )
        else:  # Если пользователь выбрал "Нет"
            await poll_answer.bot.send_message(
                chat_id=poll_answer.user.id,
                text="Хорошо, выберите место из списка.",
            )


@router.message(PollStates.waiting_for_place)
async def process_place(message: types.Message, state: FSMContext):
    """
    Обработчик ввода названия заведения.
    """
    if message.text.strip(): 
        await state.update_data(place=message.text) 
        await state.set_state(PollStates.waiting_for_time)
        await message.answer("Введите время обеда (например, 13:00):")
    else:
        await message.answer("Пожалуйста, введите название заведения.")


@router.message(PollStates.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    """
    Обработчик ввода времени.
    """
    if message.text.strip(): 
        await state.update_data(time=message.text)  
        await state.set_state(PollStates.waiting_for_comment)
        await message.answer("Введите комментарий (например, 'столик у окна'):")
    else:
        await message.answer("Пожалуйста, введите время обеда.")


@router.message(PollStates.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext):
    """
    Обработчик ввода комментария.
    """
    if message.text.strip():  
        await state.update_data(comment=message.text) 
        await state.set_state(PollStates.waiting_for_poll_end_time)
        await message.answer("Введите время окончания опроса (например, 14:45):")
    else:
        await message.answer("Пожалуйста, введите комментарий.")


@router.message(PollStates.waiting_for_poll_end_time)
async def process_poll_end_time(message: types.Message, state: FSMContext):
    """
    Обработчик ввода времени окончания опроса.
    """
    try:
        end_time = datetime.strptime(message.text, "%H:%M").time()
    except ValueError:
        await message.answer("Пожалуйста, введите время в формате ЧЧ:ММ (например, 14:45).")
        return

    now = datetime.now()
    end_datetime = datetime.combine(now.date(), end_time)

    if end_datetime <= now:
        await message.answer("Время окончания опроса должно быть в будущем.")
        return

    user_data = await state.get_data()  

    poll_message = await message.answer_poll(
        question=f"Пойти в {user_data['place']} в {user_data['time']}? ({user_data['comment']})",
        options=["Пойду", "Не пойду"],
        is_anonymous=False,  
    )

    await create_poll_use_case.save_poll(poll_message.poll.id, poll_message.poll)

    chat_id = message.chat.id
    message_id = poll_message.message_id
    time_difference = (end_datetime - now).total_seconds()

    asyncio.create_task(close_poll_at_time(message.bot, chat_id, message_id, time_difference))

    await state.clear() 


async def close_poll_at_time(bot: Bot, chat_id: int, message_id: int, delay: float):
    """
    Обработчик закрытия опроса в указанное время.
    """
    await asyncio.sleep(delay)  
    await bot.stop_poll(chat_id=chat_id, message_id=message_id)  

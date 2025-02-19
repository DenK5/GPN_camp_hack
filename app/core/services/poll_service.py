from aiogram import Bot, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import logging

class PollService:
    async def send_poll(self, chat_id: int, lunch_time: str, place_name: str, end_time: str):
        bot = Bot(token="7119550077:AAHpY8Evua6Bc0htFSZ50vU1uzautnZXLvA")
        poll_question = f"Вы хотите пойти в {lunch_time} на обед в {place_name}? Опрос заканчивается в {end_time}."
        
        options = ["Пойду", "Не пойду"]

        try:
            poll_message = await bot.send_poll(
                chat_id=chat_id,
                question=poll_question,
                options=options,
                is_anonymous=False,
                type="regular",
                allows_multiple_answers=False
            )

            if not poll_message or not poll_message.message_id:
                raise ValueError("Опрос не был успешно создан: отсутствует message_id")

            logging.info(f"Опрос для {place_name} отправлен в чат {chat_id}. message_id: {poll_message.message_id}")
            return poll_message

        except Exception as e:
            logging.error(f"Ошибка при отправке опроса: {e}")
            raise

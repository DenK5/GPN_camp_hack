from aiogram.types import Message
from aiogram import Bot

class LocationService:
    def __init__(self, bot: Bot):
        """
        Инициализация сервиса для отправки карт.
        :param bot: Экземпляр бота для отправки сообщений.
        """
        self.bot = bot

    async def send_location(self, chat_id: int, latitude: float, longitude: float) -> None:
        """
        Отправляет карту с отмеченной геопозицией.
        :param chat_id: ID чата, куда отправить карту.
        :param latitude: Широта.
        :param longitude: Долгота.
        """
        await self.bot.send_location(chat_id=chat_id, latitude=latitude, longitude=longitude)
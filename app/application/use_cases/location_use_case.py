from typing import Optional, Dict
from app.infrastructure.external.maps_api import MapsAPIClient

class LocationUseCase:
    def __init__(self, maps_api_client: MapsAPIClient):
        """
        Инициализация use case для работы с геопозицией.
        :param maps_api_client: Клиент для работы с API карт.
        """
        self.maps_api_client = maps_api_client

    async def get_location_by_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Получение геопозиции по адресу.
        :param address: Адрес для поиска.
        :return: Словарь с координатами {"latitude": float, "longitude": float} или None, если адрес не найден.
        """
        return await self.maps_api_client.geocode(address)
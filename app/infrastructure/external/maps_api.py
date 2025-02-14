import requests
from typing import Optional, Dict, Any
from config import Config

class MapsAPIClient:
    def __init__(self, api_key: str = Config.MAPS_API_KEY):
        """
        Инициализация клиента для работы с API карт.
        :param api_key: API-ключ для доступа к сервису карт.
        """
        self.api_key = api_key

    async def geocode(self, address: str) -> Optional[Dict[str, float]]:
        """
        Геокодирование адреса с использованием API карт.
        :param address: Адрес для поиска.
        :return: Словарь с координатами {"latitude": float, "longitude": float} или None, если адрес не найден.
        """
        geocode_url = f"https://catalog.api.2gis.com/3.0/items/geocode?q={address}&fields=items.point&key={self.api_key}"
        response = requests.get(geocode_url).json()

        if response.get("result") and response["result"].get("items"):
            first_item = response["result"]["items"][0]
            if "point" in first_item:
                location = first_item["point"]
                return {
                    "latitude": location["lat"],
                    "longitude": location["lon"],
                }
        return None
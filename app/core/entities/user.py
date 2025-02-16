from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    telegram_id: int
    chat_id: str
    base_position_lat: Optional[float] = None  # Широта
    base_position_lng: Optional[float] = None  # Долгота
    avg_receipt: Optional[float] = None  # Желаемый средний чек
    preferences_by_type: Optional[str] = None  # Предпочтения по типу кухни
    preferences_by_food: Optional[str] = None  # Конкретные предпочтения в еде (любимая еда, аллергии, нелюбимая еда)

    def set_avg_receipt(self, avg_receipt: float):
        """ Устанавливает средний чек пользователя. """
        self.avg_receipt = avg_receipt

    def get_avg_receipt(self) -> Optional[str]:
        """ Возвращает средний чек пользователя. """
        return self.avg_receipt

    def set_preferences_by_type(self, preferences_by_type: str):
        """ Устанавливает предпочтения пользователя по типу кухни. """
        self.preferences_by_type = preferences_by_type

    def get_preferences_by_type(self) -> Optional[str]:
        """ Возвращает предпочтения пользователя по типу кухни. """
        return self.preferences_by_type
    
    def set_preferences_by_food(self, preferences_by_food: str):
        """ Устанавливает предпочтения в еде пользователя. """
        self.preferences_by_food = preferences_by_food

    def get_preferences_by_food(self) -> Optional[str]:
        """ Возвращает предпочтения в еде пользователя. """
        return self.preferences_by_food

    def set_base_position(self, latitude: float, longitude: float):
        """ Устанавливает координаты (широту и долготу) для пользователя. """
        self.base_position_lat = latitude
        self.base_position_lng = longitude

    def get_base_position(self) -> Optional[dict]:
        """ Возвращает координаты (широту и долготу) пользователя. """
        if self.base_position_lat is not None and self.base_position_lng is not None:
            return {
                "latitude": self.base_position_lat,
                "longitude": self.base_position_lng
            }
        return None

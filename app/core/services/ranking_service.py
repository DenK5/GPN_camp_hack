# Алгоритм ранжирования (LLM, предпочтения)
# НУЖНО ДОБАВИТЬ ИМПОРТ USER
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
from app.infrastructure.external.map_api.models.Route import Route
from app.infrastructure.external.map_api.models.Point import Point
import requests


class RankingService:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @staticmethod
    def normalize(values: list[float]) -> list[float]:
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return [0.0] * len(values)  # Если все значения одинаковы, возвращаем 0
        return [(x - min_val) / (max_val - min_val) for x in values]
    
    @staticmethod
    def collect_normalization_data(places: list[PlaceInfo]) -> dict[str, list[float]]:
        data = {
            "avg_lunch_cost": [],
            "avg_business_lunch_cost": [],
            "general_rating": [],
        }
        for place in places:
            data["avg_lunch_cost"].append(place.avg_lunch_cost)
            data["avg_business_lunch_cost"].append(place.avg_business_lunch_cost)
            data["general_rating"].append(place.general_rating)
        return data
    

    def normalize_places(self, places: list[PlaceInfo]) -> list[PlaceInfo]:
        data = self.collect_normalization_data(places)
        normalized_data = {key: self.normalize(values) for key, values in data.items()}

        for i, place in enumerate(places):
            place.avg_lunch_cost = normalized_data["avg_lunch_cost"][i]
            place.avg_business_lunch_cost = normalized_data["avg_business_lunch_cost"][i]
            place.general_rating = normalized_data["general_rating"][i]
        return places


    @staticmethod
    def get_score(
        wanted_price: float,  # Желаемая цена (нормализованная)
        avg_lunch_cost: float,  # Нормализованная стоимость обеда
        avg_business_lunch_cost: float,  # Нормализованная стоимость бизнес-ланча
        place_rating: float,  # Нормализованный рейтинг
        coef_price: float = 0.28,
        coef_rating: float = 0.23,
        coef_lunch: float = 0.3
    ) -> float:
        lunch_factor = 0
        if avg_business_lunch_cost == -1:
            price = avg_lunch_cost
        else:
            price = avg_business_lunch_cost
            lunch_factor = 1

        return (wanted_price - price) * coef_price + place_rating * coef_rating + coef_lunch * lunch_factor
    
    async def get_places_score(
        self, office_point: Point, group_needs: list[User], places: list[PlaceInfo], k: int = 10, coef_time: float = 0.18
    ) -> list[PlaceInfo]:
        # Нормализуем данные
        places = self.normalize_places(places)

        # Собираем оценки
        place_scores = {place.place_id: 0 for place in places}
        for place in places:
            duration = await Map2GisAPI(self.api_key).get_route(office_point, place.point).duration
            duration_normalized = self.normalize([duration])[0]  # Нормализуем время в пути
            place_scores[place.place_id] -= duration_normalized * coef_time

            for user in group_needs:
                wanted_price_normalized = self.normalize([user.avg_receipt])[0]  # Нормализуем желаемую цену
                place_scores[place.place_id] += RankingService.get_score(
                    wanted_price_normalized,
                    place.avg_lunch_cost,
                    place.avg_business_lunch_cost,
                    place.general_rating,
                )

        # Сортируем и возвращаем top-k мест
        sorted_places = sorted(places, key=lambda x: place_scores[x.place_id], reverse=True)
        return sorted_places[:k]
        
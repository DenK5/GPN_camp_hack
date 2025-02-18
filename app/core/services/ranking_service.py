# # Алгоритм ранжирования (LLM, предпочтения)
# # НУЖНО ДОБАВИТЬ ИМПОРТ USER
# from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
# from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
# from app.infrastructure.external.map_api.models.Route import Route
# from app.infrastructure.external.map_api.models.Point import Point
# import requests


# class RankingService:
#     def __init__(self, api_key: str) -> None:
#         self._api_key = api_key

#     @staticmethod
#     def normalize(values: list[float]) -> list[float]:
#         min_val = min(values)
#         max_val = max(values)
#         if max_val == min_val:
#             return [0.0] * len(values)  # Если все значения одинаковы, возвращаем 0
#         return [(x - min_val) / (max_val - min_val) for x in values]
    
#     @staticmethod
#     def collect_normalization_data(places: list[PlaceInfo]) -> dict[str, list[float]]:
#         data = {
#             "avg_lunch_cost": [],
#             "avg_business_lunch_cost": [],
#             "general_rating": [],
#         }
#         for place in places:
#             data["avg_lunch_cost"].append(place.avg_lunch_cost)
#             data["avg_business_lunch_cost"].append(place.avg_business_lunch_cost)
#             data["general_rating"].append(place.general_rating)
#         return data
    

#     def normalize_places(self, places: list[PlaceInfo]) -> list[PlaceInfo]:
#         data = self.collect_normalization_data(places)
#         normalized_data = {key: self.normalize(values) for key, values in data.items()}

#         for i, place in enumerate(places):
#             place.avg_lunch_cost = normalized_data["avg_lunch_cost"][i]
#             place.avg_business_lunch_cost = normalized_data["avg_business_lunch_cost"][i]
#             place.general_rating = normalized_data["general_rating"][i]
#         return places


#     @staticmethod
#     def get_score(
#         wanted_price: float,  # Желаемая цена (нормализованная)
#         avg_lunch_cost: float,  # Нормализованная стоимость обеда
#         avg_business_lunch_cost: float,  # Нормализованная стоимость бизнес-ланча
#         place_rating: float,  # Нормализованный рейтинг
#         coef_price: float = 0.28,
#         coef_rating: float = 0.23,
#         coef_lunch: float = 0.3
#     ) -> float:
#         lunch_factor = 0
#         if avg_business_lunch_cost == -1:
#             price = avg_lunch_cost
#         else:
#             price = avg_business_lunch_cost
#             lunch_factor = 1

#         return (wanted_price - price) * coef_price + place_rating * coef_rating + coef_lunch * lunch_factor
    
#     async def get_places_score(
#         self, office_point: Point, group_needs: list[User], places: list[PlaceInfo], k: int = 10, coef_time: float = 0.18
#     ) -> list[PlaceInfo]:
#         # Нормализуем данные
#         places = self.normalize_places(places)

#         # Собираем оценки
#         place_scores = {place.place_id: 0 for place in places}
#         for place in places:
#             duration = await Map2GisAPI(self.api_key).get_route(office_point, place.point).duration
#             duration_normalized = self.normalize([duration])[0]  # Нормализуем время в пути
#             place_scores[place.place_id] -= duration_normalized * coef_time

#             for user in group_needs:
#                 wanted_price_normalized = self.normalize([user.avg_receipt])[0]  # Нормализуем желаемую цену
#                 place_scores[place.place_id] += RankingService.get_score(
#                     wanted_price_normalized,
#                     place.avg_lunch_cost,
#                     place.avg_business_lunch_cost,
#                     place.general_rating,
#                 )

#         # Сортируем и возвращаем top-k мест
#         sorted_places = sorted(places, key=lambda x: place_scores[x.place_id], reverse=True)
#         return sorted_places[:k]
        
        
from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from app.infrastructure.external.map_api.models.Point import Point

from pydantic import BaseModel
import numpy as np


class User(BaseModel):
    wanted_price: float
    current_lat: float
    current_lon: float


map_api = Map2GisAPI('...')       
    

class RankingService:
    async def __get_rrf_score_for_user(
        self, user: User, places: list[PlaceInfo], 
        rrf_coef: int = 3, significance_coef: np.ndarray[float] = np.array([0.282, 0.308, 0.179, 0.231])
    ) -> np.ndarray[float]:
        """Метод для оценки всех мест согласно предпочтениям данного пользователя
        """
        matrix = np.array([
            current_place.avg_lunch_cost - user.wanted_price, 
            current_place.avg_business_lunch_cost, 
            (await map_api.get_route(Point(lat=user.current_lat, lon=user.current_lon), current_place.point)).distance, 
            -current_place.general_rating
        ] for current_place in places)
       
        sorted_indices = np.argsort(matrix, axis=0)

        ranks = np.zeros_like(matrix)

        for col in range(matrix.shape[1]):
            ranks[sorted_indices[:, col], col] = np.arange(1, matrix.shape[0] + 1)
       
        return np.sum((1 / (rrf_coef + ranks)) * significance_coef, axis=1)
   
    async def __get_places_score(self, users: list[User], places: list[PlaceInfo]) -> np.ndarray[float]:
        """Метод для ранжирования мест согласно всем предпочтениям пользователей
        """
        matrix = np.array([
            await self.__get_rrf_score_for_user(user, places) for user in users
        ])
      
        return np.sum(matrix, axis=0)

    async def get_top_k_places(self, users: list[User], places: list[PlaceInfo], k: int = 10) -> list[PlaceInfo]:
        places_score = await self.__get_places_score(users, places)

        return list(np.take(places, places_score.argsort()[::-1])[:k])

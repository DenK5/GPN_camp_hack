from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from app.infrastructure.external.map_api.models.Point import Point
from app.core.entities.user import User
import numpy as np
import aiohttp
import json
from json_repair import repair_json

map_api = Map2GisAPI('...')


class RankingService:
    async def __get_rrf_score_for_user(
        self, user: User, places: list[PlaceInfo], distances: list[float],
        rrf_coef: int, significance_coef: np.ndarray[float] = np.array([0.282, 0.308, 0.231, 0.179])
    ) -> np.ndarray[float]:
        """Метод для оценки всех мест согласно предпочтениям данного пользователя
        """
        matrix = np.array([
            current_place.avg_lunch_cost - user.avg_receipt,
            current_place.avg_business_lunch_cost,
            -current_place.general_rating
        ] for current_place in places)

        matrix = np.c_[matrix, distances]

        sorted_indices = np.argsort(matrix, axis=0)

        ranks = np.zeros_like(matrix)

        for col in range(matrix.shape[1]):
            ranks[sorted_indices[:, col], col] = np.arange(
                1, matrix.shape[0] + 1)

        return np.sum((1 / (rrf_coef + ranks)) * significance_coef, axis=1)

    async def __get_places_score(self, init_user: User, users: list[User], places: list[PlaceInfo]) -> np.ndarray[float]:
        """Метод для ранжирования мест согласно всем предпочтениям пользователей
        """
        distances = [
            (await map_api.get_route(Point(lat=init_user.base_position_lat, lon=init_user.base_position_lng), current_place.point)).distance
            for current_place in places
        ]

        matrix = np.array([
            await self.__get_rrf_score_for_user(user, places, distances, len(places)) for user in users
        ])

        return np.sum(matrix, axis=0)

    async def get_top_k_places(self, users: list[User], places: list[PlaceInfo], k: int = 10) -> list[PlaceInfo]:
        """Метод для выбора k лучших мест согласно потребностям пользователей
        """
        places_score = await self.__get_places_score(users, places)

        return list(np.take(places, places_score.argsort()[::-1])[:k])

    async def get_llm_places(self, users: list[User], places: list[PlaceInfo], llm_url: str, model_name: str = 'gemma2', k: int = 10) -> list[PlaceInfo]:
        _PROMPT = """Ты - профессионально разбираешься в различных ресторанах и кафе, нужно, чтобы 
                из следующего списка отранжированных заведений вида: "Номер заведения : его название, список кухонь, список тэгов"
                Выбери 5 заведений больше всего подходящих пользователям.

                Обязательные правила:
                1) Минимум должно быть 5 ответов. Даже если все заведения не подходят. Ответ представляет собой массив чисел, содержащий номера заведений, всегда должно быть минимум 5 различных чисел в ответе.
                2) НЕ ГОВОРИ В ОТВЕТЕ ЛИШНИХ ФРАЗ.
                3) Отвечай в виде json, где answer - места для ответов, в ответе содержится минимум 5 чисел.
                {{
                    'answer1':
                    'answer2': 
                    'answer3': 
                    'answer4': 
                    'answer5':  
                }}
                Запрос пользователей:
                {query}
                Список заведений:
                {places_info}
                """
        query = ""
        for user in users:
            query += user.preferences_by_type + ' ' + user.preferences_by_food
        places_info = ""
        for i in range(len(places)):
            places_info += str(i) + ': ' + places[i].place_name + '. ' + ', '.join(
                places[i].cuisines) + '. ' + ','.join(places[i].rubrics) + '\n'
        payload = {
            "model": model_name,
            "prompt": _PROMPT.format(query=query,
                                     places_info=places_info
                                     ),
            "stream": False
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=llm_url,
                    json=payload,
                ) as response:
                    indexes = list(
                        map(int, json.loads(repair_json(response.json()['response'])).values()))
            return list(places[i] for i in indexes)
        except:
            return None

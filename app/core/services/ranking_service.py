from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from app.infrastructure.external.map_api.models.Point import Point
from app.core.entities.user import User
import numpy as np
import aiohttp
import json
from json_repair import repair_json
from config import Config

map_api = Map2GisAPI(Config.MAP_API_KEY)

class RankingService:
    async def __get_rrf_score_for_user(
        self, user: User, places: list[PlaceInfo], distances: list[float],
        rrf_coef: int, significance_coef: np.ndarray[float] = np.array([0.282, 0.308, 0.231, 0.179])
    ) -> np.ndarray[float]:
        """Метод для оценки всех мест согласно предпочтениям данного пользователя
        """
        matrix = np.array([[
            current_place.avg_lunch_cost - user.avg_receipt,
            current_place.avg_business_lunch_cost,
            -current_place.general_rating
        ] for current_place in places])
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

    async def __get_top_k_places(self, init_user: User, users: list[User], places: list[PlaceInfo], k: int = 10) -> list[PlaceInfo]:
        """Метод для выбора k лучших мест согласно потребностям пользователей
        """
        places_score = await self.__get_places_score(init_user, users, places)

        return list(np.take(places, places_score.argsort()[::-1])[:k])

    async def __get_llm_places(self, users: list[User], places: list[PlaceInfo]) -> list[PlaceInfo]:
        _PROMPT = """Ты - профессионально разбираешься в различных ресторанах и кафе, нужно, чтобы 
        из следующего списка отранжированных заведений вида: "Номер заведения : его название, список кухонь, список тэгов"
        Выбери 5 заведений больше всего подходящих пользователям.

        Обязательные правила:
        1) Минимум должно быть 5 ответов. Даже если все заведения не подходят. Ответ представляет собой массив чисел, содержащий номера заведений, всегда должно быть минимум 5 различных чисел в ответе.
        2) НЕ ГОВОРИ В ОТВЕТЕ ЛИШНИХ ФРАЗ.
        3) Отвечай в виде json, где answer - места для ответов, в ответе содержится минимум 5 чисел. Числа от 0 до 9.
        4) В ответе в json ни в коем случае не должно быть пропусков.
        {{
            'answer0':
            'answer1': 
            'answer2': 
            'answer3': 
            'answer4':  
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
            "model": Config.MODEL_NAME,
            "prompt": _PROMPT.format(query=query,
                                     places_info=places_info
                                     ),
            "stream": False
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=Config.LLM_API_URL,
                    json=payload,
                ) as response:
                    response_data = await response.json()
                    indexes = list(
                        map(int, json.loads(repair_json(response_data['response'])).values()))
            return list(places[i] for i in indexes)
        except:
            return None
        
    async def get_variants(self, init_user: User, users: list[User]):
        places = await map_api.get_places_info(lat=init_user.base_position_lat, lon=init_user.base_position_lng)
        top_10_places = await self.__get_top_k_places(init_user, users, places)
        top_5_places = await self.__get_llm_places(users, top_10_places)
        i = 0
        while top_5_places == None and i < 3:
            top_5_places = await self.__get_llm_places(users, top_10_places)
            i += 1
        return top_5_places

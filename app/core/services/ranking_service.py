# Алгоритм ранжирования (LLM, предпочтения)
from app.infrastructure.external.map_api.Map2GisAPI import Map2GisAPI
from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
from app.infrastructure.external.map_api.models.Route import Route
from app.infrastructure.external.map_api.models.Point import Point


class RankingService:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key


    @staticmethod
    def get_score(wanted_price: int, avg_lunch_cost: int, avg_buisness_lunch_cost: int,
              place_rating: float, coef_price: int = 1, coef_rating: int = 100, coef_overprice: int = 3) -> float:
        if avg_buisness_lunch_cost == -1:
            price = avg_lunch_cost
        else:
            price = avg_buisness_lunch_cost
        if price > wanted_price:
            price_score = wanted_price - price * coef_price * coef_overprice
        else:
            price_score = wanted_price - price * coef_price
        return (wanted_price - price) * coef_price + place_rating * coef_rating
    
    def get_places_score(self, office_point: Point, group_needs: list[User], places: list[PlaceInfo], k: int = 10, coef_time: int = 1) -> list[float]:
        place_scores = {place.place_id: 0 for place in places}
        for place in places:
            place_scores[place.place_id] -= Map2GisAPI(self.api_key).get_route(office_point, place.point).duration * 2 * coef_time
            for user in group_needs:
                place_scores[place.place_id] += RankingService.get_score(user.avg_receipt, place.avg_lunch_cost,
                                            place.avg_buisness_lunch_cost, place.general_rating)
        sorted_places = sorted(places, key=lambda x: place_scores[x.place_id], reverse=True)
        return sorted_places[:k]
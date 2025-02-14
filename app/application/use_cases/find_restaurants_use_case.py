from app.core.services.restaurant_service import RestaurantService

class FindRestaurantsUseCase:
    def __init__(self, restaurant_service: RestaurantService):
        self.restaurant_service = restaurant_service

    def execute(self, user_preferences, location):
        """
        Выполняет поиск ресторанов с учетом предпочтений пользователя и геолокации.
        """
        return self.restaurant_service.find_restaurants(user_preferences, location)

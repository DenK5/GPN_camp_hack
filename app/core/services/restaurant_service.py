from app.core.repositories.restaurant_repository import RestaurantRepository
from app.core.entities.restaurant import Restaurant

class RestaurantService:
    def __init__(self, restaurant_repository: RestaurantRepository):
        self.restaurant_repository = restaurant_repository

    def find_restaurants(self, user_preferences, location):
        """
        Ищет рестораны по геолокации, учитывая предпочтения пользователя.
        """
        restaurants = self.restaurant_repository.get_restaurants(location)

        # Фильтрация ресторанов по критериям пользователя
        filtered_restaurants = [
            r for r in restaurants
            if (not user_preferences.cuisine or r.cuisine in user_preferences.cuisine) and
               (not user_preferences.budget or r.price_range <= user_preferences.budget) and
               (r.rating >= user_preferences.min_rating)
        ]

        return filtered_restaurants

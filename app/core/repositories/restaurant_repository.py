from app.infrastructure.external.maps_api import MapsAPI
from app.core.entities.restaurant import Restaurant

class RestaurantRepository:
    def __init__(self):
        self.maps_api = MapsAPI()

    def get_restaurants(self, location):
        """
        Получает список ресторанов из MapsAPI и преобразует в объекты Restaurant.
        """
        raw_restaurants = self.maps_api.get_nearby_restaurants(location["latitude"], location["longitude"])

        restaurants = [
            Restaurant(
                name=data["name"],
                latitude=data["latitude"],
                longitude=data["longitude"],
                rating=data["rating"],
                cuisine=data["cuisine"],
                price_range=data["price_range"]
            ) for data in raw_restaurants
        ]

        return restaurants

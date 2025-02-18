# import random

# class MapsAPI:
#     @staticmethod
#     def get_nearby_restaurants(latitude, longitude):
#         """
#         Симуляция запроса к API карт для получения списка ресторанов.
#         """
#         mock_data = [
#             {"name": "Pizza Place", "latitude": latitude + 0.001, "longitude": longitude + 0.001,
#              "rating": round(random.uniform(3.5, 5.0), 1), "cuisine": "Italian", "price_range": random.randint(1, 3)},
#             {"name": "Sushi Bar", "latitude": latitude + 0.002, "longitude": longitude + 0.002,
#              "rating": round(random.uniform(3.5, 5.0), 1), "cuisine": "Japanese", "price_range": random.randint(2, 4)},
#             {"name": "Burger House", "latitude": latitude - 0.001, "longitude": longitude - 0.001,
#              "rating": round(random.uniform(3.5, 5.0), 1), "cuisine": "American", "price_range": random.randint(1, 2)},
#         ]
#         return mock_data

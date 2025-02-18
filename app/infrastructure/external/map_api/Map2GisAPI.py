import traceback
import aiohttp
from app.infrastructure.external.map_api.models.PlaceInfo import PlaceInfo
from app.infrastructure.external.map_api.models.Route import Route
from app.infrastructure.external.map_api.models.Point import Point


class Map2GisAPI:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def get_coords_by_address(self, address: str) -> Point | None:
        """Метод для получения долготы и широты объекта по его физическому адресу

        Args:
            address (str): Текстовое значение адреса, состоящего из города, улицы и номера дома

        Returns:
            Point | None: Значение широты и долготы в случае, если запрос прошел, иначе -- None

        Examples:
            >>> Map2GisAPI.get_coords_by_address('Санкт-Петербург, Виленский переулок, 14')
            Point('lat': 59.94028, 'lon': 30.369012)
        """
        url = 'https://catalog.api.2gis.com/3.0/items/geocode'
        params = {
            'q': address,
            'fields': 'items.point',
            'key': self._api_key
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=url,
                    params=params,
                ) as response:
                    response_data = await response.json()
            return Point(**response_data['result']['items'][0]['point'])
        except:
            return None

    async def get_city_by_point(self, point: Point) -> str:
        """Метод для получения города по координатам

        Args:
            point (Point): Долгота и широта объекта (координата)

        Returns:
            str | None: Значение города

        Examples:
            >>> Map2GisAPI.get_city_by_point(Point(lat=59.931345, lon=30.366953))
            Санкт-Петербург
        """
        url = 'https://catalog.api.2gis.com/3.0/items/geocode'
        params = {
            'lat': point.lat,
            'lon': point.lon,
            'fields': 'items.full_address_name',
            'key': self._api_key
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=url,
                    params=params,
                ) as response:
                    response_data = await response.json()
            items = response_data['result']['items']
            for item in items:
                if item.get('subtype') == 'city':
                    return item.get('name')
        except:
            return None

    async def get_places_info(self, lat: float, lon: float, query: str = 'обед с бизнес-ланчем', radius: int = 1000) -> list[PlaceInfo]:
        """Метод для получения информации об объектах в радиусе по данной широте и долготе

        Args:
            lat (float): Широта точки
            lon (float): Долгота точки
            query (float): Запрос, по которому осуществляется поиск
            radius (float): Радиус (в метрах), по которому осуществляется поиск

        Returns:
            list[PlaceInfo]: Список информации о местах общественного питания, найденный в данном радиусе относительно точки

        Examples:
            >>> Map2GisAPI.get_places_info(lat=59.94028, lon=30.369012)
            [PlaceInfo(...), ..., PlaceInfo(...)]
        """
        url = 'https://catalog.api.2gis.com/3.0/items'
        page_size = 10
        places = []
        params = {
            'q': query,
            'lon': lon,
            'lat': lat,
            'radius': radius,
            'type': 'branch',
            'fields': 'items.point,items.rubrics,items.description,items.reviews,items.statistics,items.context',
            'page': 1,
            'page_size': page_size,
            'key': self._api_key
        }

        try:
            while True:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url=url,
                        params=params,
                    ) as response:
                        response.raise_for_status()
                        response_data = await response.json()

                data = response_data.get('result', {})

                if not data:
                    break

                places.extend([place for place in data.get('items', [])])

                total = data.get('total', 0)
                if len(places) >= total:
                    break

                params['page'] += 1

        except Exception as e:
            print("Произошла ошибка:")
            traceback.print_exc()

        return [PlaceInfo(**place) for place in places]

    async def get_place_info(self, city: str, place_address: str) -> PlaceInfo | None:
        """Метод для получения информации об объекте по его адресу и названию

        Args:
            city (str): Город
            place_address (str): Текстовое значение адреса, состоящего из города, улицы и номера дома вместе с названием заведения

        Returns:
            PlaceInfo | None: Информация о заведении

        Examples:
            >>> Map2GisAPI.get_place_info(address='Омск, проспект Мира 9', place_name='Ланч-Тайм')
            PlaceInfo(...)
        """
        url = 'https://catalog.api.2gis.com/3.0/items'

        params = {
            'q': f'{city}, {place_address}',
            'type': 'branch',
            'fields': 'items.point,items.rubrics,items.description,items.reviews,items.statistics,items.context',
            'key': self._api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url=url,
                    params=params,
                ) as response:
                    response_data = await response.json()
            return PlaceInfo(**response_data['result']['items'][0])
        except:
            return None

    async def get_route(self, from_point: Point, to_point: Point) -> Route | None:
        """Метод для получения расстояния от точки до точки и времени пути

        Args:
            from_point (Point): Начальная точка
            to_point (Point): Конечная точка

        Returns:
            Route | None: Информация о маршруте

        Examples:
            >>> Map2GisAPI.get_route(Point(lat=59.942208, lon=30.355653), Point(lat=59.94156, lon=30.363407))
            Route(distance=536, duration=357)
        """
        url = 'https://routing.api.2gis.com/get_dist_matrix'

        headers = {
            'Content-Type': 'application/json'
        }

        data = {
            'points': [
                dict(from_point),
                dict(to_point)
            ],
            'sources': [0],
            'targets': [1],
            'transport': 'walking',
            'type': 'shortest',
        }

        params = {
            'key': self._api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,
                ) as response:
                    response_data = await response.json()
            return Route(**response_data['routes'][0])
        except:
            return None

    async def get_address_by_coords(self, latitude: float, longitude: float) -> str | None:
        """Метод для получения адреса по координатам (широта и долгота).

        Args:
            latitude (float): Широта точки
            longitude (float): Долгота точки

        Returns:
            str | None: Адрес объекта
        """
        url = 'https://catalog.api.2gis.com/3.0/items/geocode'
        params = {
            'lat': latitude,
            'lon': longitude,
            'fields': 'items.full_address_name',
            'key': self._api_key
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=url, params=params) as response:
                    response_data = await response.json()
            items = response_data['result']['items']
            if items:
                return items[0].get('full_address_name')
        except:
            return None

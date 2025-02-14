from app.core.entities.poll import Poll
from typing import List, Optional

class PollService:
    def __init__(self, poll_repository, restaurant_repository):
        self.poll_repository = poll_repository
        self.restaurant_repository = restaurant_repository
    
    def create_poll(self, group_id: int, filters: Optional[dict] = None) -> Optional[Poll]:
        """
        Формирует опрос с вариантами ресторанов.

        :param group_id: ID группового чата
        :param filters: Фильтры для поиска ресторанов (по желанию)
        :return: Созданный объект Poll или None, если рестораны не найдены
        """
        # Получаем список ресторанов с учетом фильтров
        restaurants = self.restaurant_repository.get_restaurants(filters)
        if not restaurants:
            # Можно здесь также отправить сообщение пользователю, что рестораны не найдены
            return None
        
        poll_options = [r.name for r in restaurants]
        
        # Создаем объект опроса
        poll = Poll(group_id=group_id, options=poll_options)
        
        # Сохраняем опрос в репозитории
        self.poll_repository.save(poll)
        
        return poll

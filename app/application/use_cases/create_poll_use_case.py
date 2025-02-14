from app.core.entities.poll import Poll
from app.core.repositories.poll_repository import PollRepository
from app.core.services.poll_service import PollService
from app.application.use_cases.find_restaurants_use_case import FindRestaurantsUseCase

class CreatePollUseCase:
    def __init__(self, poll_repository: PollRepository, poll_service: PollService,
                 find_restaurants_use_case: FindRestaurantsUseCase):
        self.poll_repository = poll_repository
        self.poll_service = poll_service
        self.find_restaurants_use_case = find_restaurants_use_case

    def execute(self, group_id: int, user_id: int, time_limit: int, allow_custom_choice: bool = False):
        """
        Создает опрос в Telegram с вариантами ресторанов.
        :param group_id: ID группового чата
        :param user_id: ID пользователя, инициировавшего опрос
        :param time_limit: Время окончания опроса (в минутах)
        :param allow_custom_choice: Разрешить пользователям предлагать свои варианты
        """
        # Получаем список ресторанов
        restaurants = self.find_restaurants_use_case.execute(group_id)
        if not restaurants:
            from app.presentation.bot.telegram_bot import TelegramBot  # Отложенный импорт
            telegram_bot = TelegramBot(token="your_telegram_token_here")
            telegram_bot.send_message(group_id, "Не удалось найти рестораны. Попробуйте позже.")
            return

        # Формируем варианты для голосования
        poll_options = [restaurant.name for restaurant in restaurants]
        if allow_custom_choice:
            poll_options.append("Предложить свой вариант")
        
        # Создаем опрос
        poll = Poll(group_id=group_id, options=poll_options, creator_id=user_id, time_limit=time_limit)
        self.poll_repository.save(poll)
        
        # Отправляем опрос в Telegram
        from app.presentation.bot.telegram_bot import TelegramBot  # Отложенный импорт
        telegram_bot = TelegramBot(token="your_telegram_token_here")
        poll_message = telegram_bot.send_poll(group_id, "Где обедаем?", poll_options)
        if not poll_message:
            telegram_bot.send_message(group_id, "Ошибка при создании опроса.")
            return

        # Привязываем сообщение Telegram к нашему опросу
        self.poll_service.link_poll_to_message(poll.id, poll_message.message_id)
        
        telegram_bot.send_message(group_id, "Голосуйте за ресторан! ⏳")

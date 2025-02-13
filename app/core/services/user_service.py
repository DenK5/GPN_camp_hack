from app.core.repositories.user_repository import UserRepository
from app.core.entities.user import User

class UserService:
    def __init__(self):
        self.user_repo = UserRepository()

    def set_avg_receipt(self, telegram_id: str, avg_receipt: float):
        """ Устанавливает средний чек пользователя. """
        return self.user_repo.update_avg_receipt(telegram_id, avg_receipt)

    def get_avg_receipt(self, telegram_id: str):
        """ Получает средний чек пользователя. """
        user = self.user_repo.get_user(telegram_id)
        return user.avg_receipt if user else None

    def set_preferences(self, telegram_id: str, preferences_by_type: str, preferences_by_food: str):
        """ Устанавливает предпочтения пользователя. """
        return self.user_repo.update_preferences(telegram_id, preferences_by_type, preferences_by_food)

    def get_preferences(self, telegram_id: str):
        """ Получает предпочтения пользователя. """
        user = self.user_repo.get_user(telegram_id)
        if user:
            return {
                "preferences_by_type": user.preferences_by_type,
                "preferences_by_food": user.preferences_by_food
            }
        return None

    def update_preferences(self, telegram_id: int, cuisine: str, avg_receipt: int, food_preferences: str):
        """ Обновляет предпочтения пользователя """
        user = self.user_repo.get_user(telegram_id)
        if not user:
            user = User(telegram_id=telegram_id, chat_id=str(telegram_id))
        
        user.set_preferences_by_type(cuisine)  # Свободный ввод кухни
        user.set_avg_receipt(avg_receipt)
        user.set_preferences_by_food(food_preferences)
        
        self.user_repo.save_user(user)
        
    def set_base_position(self, telegram_id: str, base_position: str):
        """ Устанавливает базовый адрес пользователя. """
        return self.user_repo.update_base_position(telegram_id, base_position)

    def get_base_position(self, telegram_id: str):
        """ Получает базовый адрес пользователя. """
        user = self.user_repo.get_user(telegram_id)
        return user.base_position if user else None

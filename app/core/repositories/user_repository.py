from sqlalchemy.orm import Session
from app.infrastructure.db.user_model import UserModel

class UserRepository:
    def __init__(self, db_session: Session):
        self.db = db_session

    def get_user(self, telegram_id: str) -> UserModel:
        """ Получает пользователя по telegram_id. """
        return self.db.query(UserModel).filter(UserModel.telegram_id == telegram_id).first()

    def save_user(self, user: UserModel):
        """ Сохраняет нового пользователя в БД. """
        self.db.add(user)
        self.db.commit()

    def update_avg_receipt(self, telegram_id: str, avg_receipt: float):
        """ Обновляет средний чек пользователя. """
        user = self.get_user(telegram_id)
        if user:
            user.avg_receipt = avg_receipt
            self.db.commit()
        return user

    def update_preferences(self, telegram_id: str, preferences_by_type: str, preferences_by_food: str):
        """ Обновляет предпочтения пользователя по типу кухни и конкретной еде. """
        user = self.get_user(telegram_id)
        if user:
            user.preferences_by_type = preferences_by_type
            user.preferences_by_food = preferences_by_food
            self.db.commit()
        return user

    def update_base_position(self, telegram_id: str, base_position: str):
        """ Обновляет базовый адрес пользователя. """
        user = self.get_user(telegram_id)
        if user:
            user.base_position = base_position
            self.db.commit()
        return user

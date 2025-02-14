from app.core.repositories.user_repository import UserRepository
from app.core.entities.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.base import AsyncSessionLocal


class UserService:
    def __init__(self, db_session: AsyncSession = None):
        """
        Инициализация сервиса пользователя с передачей сессии базы данных.
        Если сессия не передана, создаем новую.
        """
        self.db_session = db_session or AsyncSessionLocal()
        self.user_repo = UserRepository(self.db_session)

    async def set_avg_receipt(self, telegram_id: int, avg_receipt: float):
        """
        Устанавливает средний чек пользователя.
        """
        return await self.user_repo.update_avg_receipt(telegram_id, avg_receipt)

    async def get_avg_receipt(self, telegram_id: int):
        """
        Получает средний чек пользователя.
        """
        user = await self.user_repo.get_user(telegram_id)
        return user.avg_receipt if user else None

    async def set_preferences(self, telegram_id: int, preferences_by_type: str, preferences_by_food: str):
        """
        Устанавливает предпочтения пользователя.
        """
        return await self.user_repo.update_preferences(telegram_id, preferences_by_type, preferences_by_food)

    async def get_preferences(self, telegram_id: int):
        """
        Получает предпочтения пользователя.
        """
        user = await self.user_repo.get_user(telegram_id)
        if user:
            return {
                "preferences_by_type": user.preferences_by_type,
                "preferences_by_food": user.preferences_by_food
            }
        return None

    async def update_preferences(self, telegram_id: int, cuisine: str, avg_receipt: float, food_preferences: str):
        """
        Обновляет предпочтения пользователя (кухня, средний чек, предпочтения по еде).
        Если пользователя нет в БД, создаем нового и сохраняем.
        """
        user = await self.user_repo.get_user(telegram_id)

        if not user:
            user = User(
                telegram_id=telegram_id, 
                chat_id=str(telegram_id), 
                base_position=None
            )
            await self.user_repo.save_user(user)

        user.set_preferences_by_type(cuisine)
        user.set_avg_receipt(avg_receipt)
        user.set_preferences_by_food(food_preferences)

        await self.user_repo.save_user(user)

        return user


    async def set_base_position(self, telegram_id: int, base_position: str):
        """
        Устанавливает базовый адрес пользователя и сохраняет его в базе данных.
        """
        user = await self.user_repo.get_user(telegram_id)
        if user:
            user.base_position = base_position
            await self.user_repo.save_user(user)
            return True
        return False

    async def get_base_position(self, telegram_id: int):
        """
        Получает базовый адрес пользователя.
        """
        user = await self.user_repo.get_user(telegram_id)
        return user.base_position if user else None

    async def close(self):
        """Закрываем сессию при уничтожении объекта сервиса."""
        await self.db_session.close()

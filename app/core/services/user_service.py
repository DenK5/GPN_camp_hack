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

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.db_session.close()

    async def get_user_data(self, telegram_id: int):
        """
        Получает все данные пользователя (координаты, средний чек, предпочтения).
        """
        user = await self.user_repo.get_user(telegram_id)
        if user:
            return {
                "telegram_id": user.telegram_id,
                "chat_id": user.chat_id,
                "base_position_lat": user.base_position_lat,
                "base_position_lng": user.base_position_lng,
                "avg_receipt": user.avg_receipt,
                "preferences_by_type": user.preferences_by_type,
                "preferences_by_food": user.preferences_by_food
            }
        return None
    
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
        user = await self.user_repo.get_user(telegram_id)

        if not user:
            user = User(
                telegram_id=telegram_id, 
                chat_id=str(telegram_id), 
                base_position_lat=None,
                base_position_lng=None,
                avg_receipt=avg_receipt,
                preferences_by_type=cuisine,
                preferences_by_food=food_preferences
            )
            await self.user_repo.save_user(user)
        else:
            user.avg_receipt = avg_receipt
            user.preferences_by_type = cuisine
            user.preferences_by_food = food_preferences
            await self.user_repo.save_user(user)

        await self.db_session.commit()
        return user

    async def set_base_position(self, telegram_id: int, latitude: float, longitude: float):
        user = await self.user_repo.get_user(telegram_id)

        if not user:
            user = User(
                telegram_id=telegram_id, 
                chat_id=str(telegram_id),
                avg_receipt=None,
                preferences_by_type=None,
                preferences_by_food=None,
                base_position_lat=latitude,
                base_position_lng=longitude 
            )
            await self.user_repo.save_user(user)  
        else:
            user.base_position_lat = float(latitude)
            user.base_position_lng = float(longitude)
            await self.user_repo.save_user(user)  

        await self.db_session.commit()
        return True

    async def get_base_position(self, telegram_id: int):
        """
        Получает базовые координаты (широту и долготу) пользователя.
        """
        user = await self.user_repo.get_user(telegram_id)
        if user:
            return {
                "latitude": user.base_position_lat,
                "longitude": user.base_position_lng
            }
        return None

    async def save_user_data(self, telegram_id: int, cuisine: str, avg_receipt: float, food_preferences: str, latitude: float, longitude: float):
        """
        Сохраняет все данные пользователя, включая предпочтения, средний чек и координаты.
        """
        user = await self.user_repo.get_user(telegram_id)

        if not user:
            user = User(
                telegram_id=telegram_id, 
                chat_id=str(telegram_id), 
                avg_receipt=avg_receipt,
                preferences_by_type=cuisine,
                preferences_by_food=food_preferences,
                base_position_lat=latitude,
                base_position_lng=longitude
            )
            await self.user_repo.save_user(user)
        else:
            user.avg_receipt = avg_receipt
            user.preferences_by_type = cuisine
            user.preferences_by_food = food_preferences
            user.base_position_lat = latitude
            user.base_position_lng = longitude
            await self.user_repo.save_user(user)

        await self.db_session.commit()
        return user

    async def close(self):
        """Закрываем сессию при уничтожении объекта сервиса."""
        await self.db_session.close()

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.infrastructure.db.user_model import UserModel
from app.core.entities.user import User
from sqlalchemy.exc import IntegrityError

class UserRepository:
    def __init__(self, db_session: AsyncSession):
        """
        Инициализация репозитория с использованием асинхронной сессии базы данных.
        """
        self.db = db_session

    async def get_user(self, telegram_id: int) -> User:
        """
        Получает пользователя по telegram_id.
        """
        stmt = select(UserModel).filter(UserModel.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            return User(
                telegram_id=user_model.telegram_id,
                chat_id=user_model.chat_id,
                avg_receipt=user_model.avg_receipt,
                preferences_by_type=user_model.preferences_by_type,
                preferences_by_food=user_model.preferences_by_food,
                base_position=user_model.base_position
            )
        return None

    async def save_user(self, user: User):
        """
        Сохраняет нового пользователя в БД, только если base_position не None.
        """
        if not user.base_position:
            raise ValueError("Base position must not be None")

        existing_user = await self.get_user_by_chat_id(user.chat_id)
        if existing_user:
            raise IntegrityError(f"User with chat_id {user.chat_id} already exists.", None, None)

        user_model = UserModel(
            telegram_id=user.telegram_id,
            chat_id=user.chat_id,
            avg_receipt=user.avg_receipt,
            preferences_by_type=user.preferences_by_type,
            preferences_by_food=user.preferences_by_food,
            base_position=user.base_position
        )
        self.db.add(user_model)
        try:
            await self.db.commit()
        except IntegrityError as e:

            await self.db.rollback()
            raise e

    async def update_avg_receipt(self, telegram_id: int, avg_receipt: float) -> User:
        """
        Обновляет средний чек пользователя.
        """
        user = await self.get_user(telegram_id)
        if user:
            user.avg_receipt = avg_receipt
            await self.db.commit()
            return user
        return None

    async def update_preferences(self, telegram_id: int, preferences_by_type: str, preferences_by_food: str) -> User:
        """
        Обновляет предпочтения пользователя по кухне и еде.
        """
        user = await self.get_user(telegram_id)
        if user:
            user.preferences_by_type = preferences_by_type
            user.preferences_by_food = preferences_by_food
            await self.db.commit()
            return user
        return None

    async def update_base_position(self, telegram_id: int, base_position: str) -> User:
        """
        Обновляет базовый адрес пользователя.
        """
        if not base_position:
            raise ValueError("Base position must not be None")
        
        user = await self.get_user(telegram_id)
        if user:
            user.base_position = base_position
            await self.db.commit()
            return user
        return None

    async def get_user_by_chat_id(self, chat_id: str) -> User:
        """
        Получает пользователя по chat_id.
        """
        stmt = select(UserModel).filter(UserModel.chat_id == chat_id)
        result = await self.db.execute(stmt)
        user_model = result.scalars().first()
        if user_model:
            return User(
                telegram_id=user_model.telegram_id,
                chat_id=user_model.chat_id,
                avg_receipt=user_model.avg_receipt,
                preferences_by_type=user_model.preferences_by_type,
                preferences_by_food=user_model.preferences_by_food,
                base_position=user_model.base_position
            )
        return None

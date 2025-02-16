from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.infrastructure.db.base import AsyncSessionLocal
from app.core.repositories.user_repository import UserRepository
from app.core.repositories.restaurant_repository import RestaurantRepository
from app.core.repositories.poll_repository import PollRepository
from app.core.repositories.group_repository import GroupRepository

class UnitOfWork:
    def __init__(self, db_session: AsyncSession = None):
        """
        Инициализация Unit of Work с использованием сессии базы данных.
        """
        self.db_session = db_session or AsyncSessionLocal()
        self.user_repo = UserRepository(self.db_session)
        self.restaurant_repo = RestaurantRepository(self.db_session)
        self.poll_repo = PollRepository(self.db_session)
        self.group_repo = GroupRepository(self.db_session)

    async def commit(self):
        """
        Завершаем транзакцию, применяя все изменения.
        """
        try:
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            raise e

    async def rollback(self):
        """
        Откатывает транзакцию, если что-то пошло не так.
        """
        await self.db_session.rollback()

    async def close(self):
        """
        Закрываем сессию базы данных.
        """
        await self.db_session.close()

    def __enter__(self):
        """
        Включает поддержку контекста сессии (для использования 'with' statement).
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Закрытие сессии и откат в случае ошибки при использовании с 'with' statement.
        """
        if exc_type is None:
            self.db_session.commit()
        else:
            self.db_session.rollback()
        self.db_session.close()

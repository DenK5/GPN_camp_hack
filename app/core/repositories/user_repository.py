import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.infrastructure.db.user_model import UserModel
from app.core.entities.user import User
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

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
        logger.info(f"🔎 Поиск пользователя с telegram_id={telegram_id} в БД")
        stmt = select(UserModel).filter(UserModel.telegram_id == telegram_id)
        result = await self.db.execute(stmt)
        user_model = result.scalars().first()
        
        if user_model:
            logger.info(f"✅ Пользователь найден: {user_model}")
            return self._map_user_model_to_entity(user_model)
        else:
            logger.warning(f"⚠️ Пользователь с telegram_id={telegram_id} не найден")
            return None

    async def save_user(self, user: User):
        """
        Сохраняет пользователя в БД, проверяя на существование.
        Если пользователь существует, обновляем данные.
        """
        logger.info(f"💾 Сохранение пользователя: {user}")
        if not user.chat_id or not user.telegram_id:
            logger.error(f"❌ Ошибка: chat_id или telegram_id пусты для пользователя: {user}")
            return None

        existing_user = await self.get_user_by_chat_id(user.chat_id)

        if existing_user:
            logger.info(f"🔄 Обновление существующего пользователя: {existing_user}")
            self._update_user_model_from_entity(existing_user, user)
            await self.db.commit()
            return existing_user
        else:
            logger.info(f"➕ Создание нового пользователя: {user}")
            user_model = self._map_user_entity_to_model(user)
            self.db.add(user_model)
            try:
                await self.db.commit()
                logger.info("✅ Пользователь успешно сохранен в БД")
            except IntegrityError as e:
                await self.db.rollback()
                logger.error(f"❌ Ошибка сохранения пользователя: {e}")
                raise e
            return user

    async def update_avg_receipt(self, telegram_id: int, avg_receipt: float) -> User:
        """
        Обновляет средний чек пользователя.
        """
        logger.info(f"💲 Обновление среднего чека пользователя {telegram_id}: {avg_receipt}")
        user = await self.get_user(telegram_id)
        if user:
            user.avg_receipt = avg_receipt
            await self.db.commit()
            logger.info(f"✅ Средний чек обновлен: {user}")
            return user
        logger.warning(f"⚠️ Пользователь {telegram_id} не найден, чек не обновлен")
        return None

    async def update_preferences(self, telegram_id: int, preferences_by_type: str, preferences_by_food: str) -> User:
        """
        Обновляет предпочтения пользователя по кухне и еде.
        """
        logger.info(f"🍽 Обновление предпочтений {telegram_id}: кухня={preferences_by_type}, еда={preferences_by_food}")
        user = await self.get_user(telegram_id)
        if user:
            user.preferences_by_type = preferences_by_type
            user.preferences_by_food = preferences_by_food
            await self.db.commit()
            logger.info(f"✅ Предпочтения обновлены: {user}")
            return user
        logger.warning(f"⚠️ Пользователь {telegram_id} не найден, предпочтения не обновлены")
        return None

    async def update_base_position(self, telegram_id: int, latitude: float, longitude: float) -> User:
        user = await self.get_user(telegram_id)

        if not user:
            logging.info(f"👤 Пользователь {telegram_id} не найден. Создаю нового...")
            user = await self.create_user(telegram_id)

        user.set_base_position(latitude, longitude)
        await self.db.commit()

        logging.info(f"✅ Базовая позиция пользователя {telegram_id} обновлена: {latitude}, {longitude}")
        return user
    
    async def create_user(self, telegram_id: int) -> User:
        new_user = User(
            telegram_id=telegram_id,
            chat_id=str(telegram_id),
            avg_receipt=None,
            preferences_by_type=None,
            preferences_by_food=None,
            base_position_lat=None,
            base_position_lng=None
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        logging.info(f"✅ Новый пользователь {telegram_id} создан в БД")
        return new_user


    async def get_user_by_chat_id(self, chat_id: str) -> User:
        """
        Получает пользователя по chat_id.
        """
        logger.info(f"🔎 Поиск пользователя по chat_id={chat_id}")
        stmt = select(UserModel).filter(UserModel.chat_id == chat_id)
        result = await self.db.execute(stmt)
        user_model = result.scalars().first()
        
        if user_model:
            logger.info(f"✅ Пользователь найден: {user_model}")
            return self._map_user_model_to_entity(user_model)
        else:
            logger.warning(f"⚠️ Пользователь с chat_id={chat_id} не найден")
            return None

    def _map_user_model_to_entity(self, user_model: UserModel) -> User:
        """
        Преобразует модель UserModel в сущность User.
        """
        return User(
            telegram_id=user_model.telegram_id,
            chat_id=user_model.chat_id,
            avg_receipt=user_model.avg_receipt,
            preferences_by_type=user_model.preferences_by_type,
            preferences_by_food=user_model.preferences_by_food,
            base_position_lat=user_model.base_position_lat,
            base_position_lng=user_model.base_position_lng
        )

    def _map_user_entity_to_model(self, user: User) -> UserModel:
        """
        Преобразует сущность User в модель UserModel для сохранения в базу данных.
        """
        return UserModel(
            telegram_id=user.telegram_id,
            chat_id=user.chat_id,
            avg_receipt=user.avg_receipt,
            preferences_by_type=user.preferences_by_type,
            preferences_by_food=user.preferences_by_food,
            base_position_lat=user.base_position_lat,
            base_position_lng=user.base_position_lng
        )

    def _update_user_model_from_entity(self, user_model: UserModel, user: User):
        """
        Обновляет модель UserModel на основе данных из сущности User.
        """
        user_model.telegram_id = user.telegram_id
        user_model.chat_id = user.chat_id
        user_model.avg_receipt = user.avg_receipt
        user_model.preferences_by_type = user.preferences_by_type
        user_model.preferences_by_food = user.preferences_by_food
        user_model.base_position_lat = user.base_position_lat
        user_model.base_position_lng = user.base_position_lng

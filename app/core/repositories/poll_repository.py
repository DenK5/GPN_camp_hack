# from app.core.entities.poll import Poll
# from app.infrastructure.db.base import BaseRepository
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy.orm import selectinload
# from app.infrastructure.db import PollModel
# from sqlalchemy.exc import NoResultFound
# import datetime

# class PollRepository(BaseRepository):
#     def __init__(self, session: AsyncSession):
#         super().__init__(session)
    
#     async def save(self, poll: Poll) -> None:
#         """Сохранение нового опроса в базу данных."""
#         poll_model = PollModel(
#             chat_id=poll.chat_id,
#             place_name=poll.place_name,
#             end_time=poll.end_time,
#             created_at=poll.created_at
#         )
#         self.session.add(poll_model)
#         await self.session.commit()
    
#     async def get_poll_by_chat_id(self, chat_id: int) -> Poll:
#         """Получение опроса по chat_id."""
#         result = await self.session.execute(select(PollModel).filter(PollModel.chat_id == chat_id))
#         poll_model = result.scalars().first()
        
#         if poll_model is None:
#             raise NoResultFound(f"Poll with chat_id {chat_id} not found.")
        
#         return Poll(
#             chat_id=poll_model.chat_id,
#             place_name=poll_model.place_name,
#             end_time=poll_model.end_time,
#             created_at=poll_model.created_at
#         )
    
#     async def get_all_polls(self) -> list:
#         """Получение всех опросов."""
#         result = await self.session.execute(select(PollModel))
#         poll_models = result.scalars().all()
        
#         polls = [
#             Poll(
#                 chat_id=poll_model.chat_id,
#                 place_name=poll_model.place_name,
#                 end_time=poll_model.end_time,
#                 created_at=poll_model.created_at
#             )
#             for poll_model in poll_models
#         ]
        
#         return polls
    
#     async def get_active_polls(self) -> list:
#         """Получение активных опросов (которые еще не завершились)."""
#         result = await self.session.execute(select(PollModel).filter(PollModel.end_time > datetime.now()))
#         poll_models = result.scalars().all()
        
#         active_polls = [
#             Poll(
#                 chat_id=poll_model.chat_id,
#                 place_name=poll_model.place_name,
#                 end_time=poll_model.end_time,
#                 created_at=poll_model.created_at
#             )
#             for poll_model in poll_models
#         ]
        
#         return active_polls

# from sqlalchemy import Column, Integer, String, DateTime
# from sqlalchemy.orm import relationship
# from datetime import datetime
# from app.infrastructure.db.base import Base

# class PollModel(Base):
#     __tablename__ = "polls"
    
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     chat_id = Column(Integer, nullable=False)
#     place_name = Column(String, nullable=False)
#     end_time = Column(DateTime, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
    
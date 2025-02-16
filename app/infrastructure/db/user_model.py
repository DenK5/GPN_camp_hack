from sqlalchemy import Integer, Column, String, Float
from app.infrastructure.db.base import Base

class UserModel(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True, unique=True, nullable=False)
    chat_id = Column(String, unique=True, nullable=False)
    avg_receipt = Column(Float, nullable=True)
    preferences_by_type = Column(String, nullable=True)
    preferences_by_food = Column(String, nullable=True)
    base_position_lat = Column(Float, nullable=True)
    base_position_lng = Column(Float, nullable=True)

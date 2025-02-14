from datetime import datetime
from pydantic import BaseModel

class Poll(BaseModel):
    question: str
    options: list[str]
    end_time: datetime
    is_closed: bool = False
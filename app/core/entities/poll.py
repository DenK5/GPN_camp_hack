from datetime import datetime

class Poll:
    def __init__(self, chat_id: int, place_name: str, end_time: str):
        self.chat_id = chat_id
        self.place_name = place_name
        self.end_time = end_time
        self.created_at = datetime.now()

    def is_active(self):
        return datetime.now() < self.end_time

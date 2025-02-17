from pydantic import BaseModel


class Route(BaseModel):
    distance: int
    duration: int

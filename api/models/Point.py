from pydantic import BaseModel


class Point(BaseModel):
    lat: float
    lon: float

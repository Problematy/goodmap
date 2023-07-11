from pydantic import BaseModel


class Coordinates(BaseModel):
    x: float
    y: float

class Location(BaseModel):
    name: str
    coordinates: Coordinates

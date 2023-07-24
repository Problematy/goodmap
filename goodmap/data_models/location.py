from pydantic import BaseModel, validator


class Location(BaseModel):
    name: str
    coordinates: tuple[float, float]

    @validator("coordinates")
    def coordinates_must_be_valid(cls, v):
        if v[0] < -90 or v[0] > 90:
            raise ValueError("latitude must be in range -90 to 90")
        if v[1] < -180 or v[1] > 180:
            raise ValueError("longitude must be in range -180 to 180")
        return v

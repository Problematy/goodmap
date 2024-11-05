from pydantic import BaseModel, create_model, field_validator


class LocationBase(BaseModel):
    position: tuple[float, float]
    UUID: str

    @field_validator("position")
    @classmethod
    def position_must_be_valid(cls, v):
        if v[0] < -90 or v[0] > 90:
            raise ValueError("latitude must be in range -90 to 90")
        if v[1] < -180 or v[1] > 180:
            raise ValueError("longitude must be in range -180 to 180")
        return v

    def basic_info(self):
        return {"UUID": self.UUID, "position": self.position}


# Generowanie dynamicznego modelu na podstawie konfiguracji
def create_location_model(obligatory_fields):
    fields = {field: (str, ...) for field in obligatory_fields}
    Location = create_model("Location", **fields, __base__=LocationBase)
    return Location

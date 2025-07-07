from typing import Any, Type

from pydantic import BaseModel, Field, create_model, field_validator


class LocationBase(BaseModel, extra="allow"):
    position: tuple[float, float]
    uuid: str
    remark: str = ""

    @field_validator("position")
    @classmethod
    def position_must_be_valid(cls, v):
        if v[0] < -90 or v[0] > 90:
            raise ValueError("latitude must be in range -90 to 90")
        if v[1] < -180 or v[1] > 180:
            raise ValueError("longitude must be in range -180 to 180")
        return v

    def basic_info(self):
        return {"uuid": self.uuid, "position": self.position, "remark": bool(self.remark)}


def create_location_model(obligatory_fields: list[tuple[str, Type[Any]]]) -> Type[BaseModel]:
    fields = {
        field_name: (field_type, Field(...)) for (field_name, field_type) in obligatory_fields
    }

    return create_model(
        "Location",
        __config__=None,
        __doc__=None,
        __module__="Location",
        __validators__=None,
        __base__=LocationBase,
        __cls_kwargs__=None,
        **fields,
    )

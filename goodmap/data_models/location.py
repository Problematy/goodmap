"""Pydantic models for location data validation and schema generation."""

from typing import Any, Type, cast

from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    create_model,
    field_validator,
    model_validator,
)

from goodmap.exceptions import LocationValidationError


class LocationBase(BaseModel, extra="allow"):
    """Base model for location data with position validation and error enrichment.

    Attributes:
        position: Tuple of (latitude, longitude) coordinates
        uuid: Unique identifier for the location
    """

    position: tuple[float, float]
    uuid: str

    @field_validator("position")
    @classmethod
    def position_must_be_valid(cls, v):
        """Validate that latitude and longitude are within valid ranges."""
        if v[0] < -90 or v[0] > 90:
            raise ValueError("latitude must be in range -90 to 90")
        if v[1] < -180 or v[1] > 180:
            raise ValueError("longitude must be in range -180 to 180")
        return v

    @model_validator(mode="before")
    @classmethod
    def validate_uuid_exists(cls, data: Any) -> Any:
        """Ensure UUID is present before validation for better error messages."""
        if isinstance(data, dict) and "uuid" not in data:
            raise ValueError("Location data must include 'uuid' field")
        return data

    @model_validator(mode="wrap")
    @classmethod
    def enrich_validation_errors(cls, data, handler):
        """Wrap validation errors with UUID context for better debugging."""
        try:
            return handler(data)
        except ValidationError as e:
            uuid = data.get("uuid") if isinstance(data, dict) else None
            raise LocationValidationError(e, uuid=uuid) from e

    def basic_info(self):
        """Get basic location information summary.

        Returns:
            dict: Dictionary with uuid, position, and remark flag
        """
        return {
            "uuid": self.uuid,
            "position": self.position,
            "remark": bool(getattr(self, "remark", False)),
        }


def create_location_model(obligatory_fields: list[tuple[str, Type[Any]]]) -> Type[BaseModel]:
    """Dynamically create a Location model with additional required fields.

    Args:
        obligatory_fields: List of (field_name, field_type) tuples for required fields

    Returns:
        Type[BaseModel]: A Location model class extending LocationBase with additional fields
    """
    fields = {
        field_name: (field_type, Field(...)) for (field_name, field_type) in obligatory_fields
    }

    return create_model(
        "Location",
        __base__=LocationBase,
        __module__="goodmap.data_models.location",
        **cast(dict[str, Any], fields),
    )

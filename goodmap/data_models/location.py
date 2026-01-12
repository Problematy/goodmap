"""Pydantic models for location data validation and schema generation."""

from typing import Annotated, Any, Type, cast

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


def create_location_model(
    obligatory_fields: list[tuple[str, str]], categories: dict[str, list[str]] = None
) -> Type[BaseModel]:
    """Dynamically create a Location model with additional required fields.

    Args:
        obligatory_fields: List of (field_name, field_type) tuples for required fields
        categories: Optional dict mapping field names to allowed values (enums)

    Returns:
        Type[BaseModel]: A Location model class extending LocationBase with additional fields
    """
    from pydantic import field_validator as pydantic_field_validator

    categories = categories or {}
    fields = {}
    validators = {}

    # Map type strings to Python types
    type_mapping = {"str": str, "list": list, "int": int, "float": float, "bool": bool, "dict": dict}

    for field_name, field_type_str in obligatory_fields:
        # Determine base type from string
        is_list = isinstance(field_type_str, str) and field_type_str.startswith("list")
        base_type = list if is_list else type_mapping.get(field_type_str, str) if isinstance(field_type_str, str) else field_type_str

        # Get category constraints if available
        allowed_values = categories.get(field_name)
        description = f"Allowed values: {', '.join(allowed_values)}" if allowed_values else None

        if allowed_values:
            # Add field with category metadata
            if is_list:
                fields[field_name] = (
                    list[str],
                    Field(..., description=description, json_schema_extra={"enum_items": allowed_values}),
                )
                # Create validator for list items
                def make_list_validator(allowed):
                    def validator(cls, v):
                        for item in v:
                            if item not in allowed:
                                raise ValueError(f"must be one of {allowed}, got '{item}'")
                        return v
                    return validator
                validators[field_name] = pydantic_field_validator(field_name)(make_list_validator(allowed_values))
            else:
                fields[field_name] = (
                    str,
                    Field(..., description=description, json_schema_extra={"enum": allowed_values}),
                )
                # Create validator for string value
                def make_str_validator(allowed):
                    def validator(cls, v):
                        if v not in allowed:
                            raise ValueError(f"must be one of {allowed}, got '{v}'")
                        return v
                    return validator
                validators[field_name] = pydantic_field_validator(field_name)(make_str_validator(allowed_values))
        else:
            # No categories, use the base type
            fields[field_name] = (base_type, Field(...))

    # Create model with validators
    model = create_model(
        "Location",
        __base__=LocationBase,
        __module__="goodmap.data_models.location",
        __validators__=validators,
        **cast(dict[str, Any], fields),
    )

    return model

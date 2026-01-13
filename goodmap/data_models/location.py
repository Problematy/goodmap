"""Pydantic models for location data validation and schema generation."""

import warnings
from typing import Any, Sequence, Type, Union, cast, overload

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
    uuid: str = Field(..., max_length=100)  # UUID is 36 chars, allow some flexibility

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


@overload
def create_location_model(
    obligatory_fields: Sequence[tuple[str, str]],
    categories: dict[str, list[str]] | None = ...,
) -> Type[BaseModel]:
    """Create location model with string type names (recommended)."""
    ...


@overload
def create_location_model(
    obligatory_fields: Sequence[tuple[str, Type[Any]]],
    categories: dict[str, list[str]] | None = ...,
) -> Type[BaseModel]:
    """Create location model with Python type objects (deprecated)."""
    ...


def create_location_model(
    obligatory_fields: Sequence[tuple[str, Union[str, Type[Any]]]],
    categories: dict[str, list[str]] | None = None,
) -> Type[BaseModel]:
    """Dynamically create a Location model with additional required fields.

    Supports both string type names (recommended) and Python type objects (deprecated).

    Args:
        obligatory_fields: List of (field_name, field_type) tuples for required fields.
                          field_type can be either:
                          - String type name: "str", "list", "int", "float", "bool", "dict"
                          - Python type object: str, list, int, etc. (deprecated)
        categories: Optional dict mapping field names to allowed values (enums)

    Returns:
        Type[BaseModel]: A Location model class extending LocationBase with additional fields

    Examples:
        >>> # Recommended: String type names
        >>> model = create_location_model([("name", "str"), ("tags", "list")])

        >>> # Deprecated: Python type objects (supported for backward compatibility)
        >>> model = create_location_model([("name", str), ("tags", list)])
    """
    from pydantic import field_validator as pydantic_field_validator

    categories = categories or {}
    fields = {}
    validators = {}

    # Map type strings to Python types
    type_mapping = {
        "str": str,
        "list": list,
        "int": int,
        "float": float,
        "bool": bool,
        "dict": dict,
    }

    for field_name, field_type_input in obligatory_fields:
        # Backward compatibility: Convert Python type objects to strings
        if isinstance(field_type_input, type):
            warnings.warn(
                f"Passing Python type objects to create_location_model is deprecated. "
                f"Use string type names instead: '{field_type_input.__name__}' "
                f"instead of {field_type_input}. "
                f"Support for type objects will be removed in version 2.0.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            # Convert type to string name
            field_type_str = field_type_input.__name__
        else:
            field_type_str = field_type_input

        # Determine base type from string
        is_list = field_type_str.startswith("list")
        base_type = list if is_list else type_mapping.get(field_type_str, str)

        # Get category constraints if available
        allowed_values = categories.get(field_name)
        description = f"Allowed values: {', '.join(allowed_values)}" if allowed_values else None

        if allowed_values:
            # Add field with category metadata
            if is_list:
                fields[field_name] = (
                    list[str],
                    Field(
                        ...,
                        description=description,
                        max_length=20,  # Max 20 items in list
                        json_schema_extra=cast(Any, {"enum_items": allowed_values}),
                    ),
                )

                # Create validator for list items
                def make_list_validator(allowed):
                    def validator(cls, v):
                        for item in v:
                            if item not in allowed:
                                raise ValueError(f"must be one of {allowed}, got '{item}'")
                            if len(item) > 100:
                                raise ValueError(
                                    f"list item too long (max 100 chars), got {len(item)}"
                                )
                        return v

                    return validator

                validators[field_name] = pydantic_field_validator(field_name)(
                    make_list_validator(allowed_values)
                )
            else:
                fields[field_name] = (
                    str,
                    Field(
                        ...,
                        description=description,
                        max_length=200,  # Max 200 chars for string fields
                        json_schema_extra=cast(Any, {"enum": allowed_values}),
                    ),
                )

                # Create validator for string value
                def make_str_validator(allowed):
                    def validator(cls, v):
                        if v not in allowed:
                            raise ValueError(f"must be one of {allowed}, got '{v}'")
                        return v

                    return validator

                validators[field_name] = pydantic_field_validator(field_name)(
                    make_str_validator(allowed_values)
                )
        else:
            # No categories, use the base type with size constraints
            if is_list:
                fields[field_name] = (
                    base_type,
                    Field(..., max_length=20),  # Max 20 items in list
                )

                # Add validator for list item length
                def make_list_length_validator():
                    def validator(cls, v):
                        for item in v:
                            if isinstance(item, str) and len(item) > 100:
                                raise ValueError(
                                    f"list item too long (max 100 chars), got {len(item)}"
                                )
                        return v

                    return validator

                validators[field_name] = pydantic_field_validator(field_name)(
                    make_list_length_validator()
                )
            elif base_type is str:
                fields[field_name] = (
                    base_type,
                    Field(..., max_length=200),  # Max 200 chars for string fields
                )
            else:
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

"""Pydantic models for location data validation and schema generation."""

import warnings
from typing import Annotated, Any, Type, cast

from annotated_types import Ge, Le
from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    ValidationError,
    create_model,
    model_validator,
)

from goodmap.exceptions import LocationValidationError

Latitude = Annotated[float, Ge(-90), Le(90)]
Longitude = Annotated[float, Ge(-180), Le(180)]


class LocationBase(BaseModel, extra="allow"):
    """Base model for location data with position validation and error enrichment.

    Attributes:
        position: Tuple of (latitude, longitude) coordinates
        uuid: Unique identifier for the location
        remark: Optional remark text for the location
    """

    position: tuple[Latitude, Longitude]
    uuid: str = Field(..., max_length=100)  # TODO make this UUID and deprecate string
    remark: str | None = None

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

    def model_dump(self, **kwargs) -> dict[str, Any]:
        """Serialize model, excluding None values by default for backward compatibility."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)

    def basic_info(self) -> dict[str, Any]:
        """Get basic location information summary."""
        data = self.model_dump(include={"uuid", "position"})
        data["remark"] = bool(self.remark)
        return data


_TYPE_MAPPING: dict[str, type] = {
    "str": str,
    "list": list,
    "int": int,
    "float": float,
    "bool": bool,
    "dict": dict,
}

_MAX_LIST_ITEM_LENGTH = 100


def _make_list_validator(allowed: list[str] | None):
    """Create a validator for list items with optional enum constraint."""

    def validate(v: list[Any]) -> list[Any]:
        for item in v:
            if allowed is not None and item not in allowed:
                raise ValueError(f"must be one of {allowed}, got '{item}'")
            if isinstance(item, str) and len(item) > _MAX_LIST_ITEM_LENGTH:
                raise ValueError(
                    f"list item too long (max {_MAX_LIST_ITEM_LENGTH} chars), got {len(item)}"
                )
        return v

    return validate


def _make_str_validator(allowed: list[str]):
    """Create a validator that checks string value is in allowed list."""

    def validate(v: str) -> str:
        if v not in allowed:
            raise ValueError(f"must be one of {allowed}, got '{v}'")
        return v

    return validate


def _normalize_field_type(field_type_input: str | Type[Any]) -> str:
    """Convert field type input to string, emitting deprecation warning for type objects."""
    if isinstance(field_type_input, type):
        warnings.warn(
            f"Passing Python type objects to create_location_model is deprecated. "
            f"Use string type names instead: '{field_type_input.__name__}' "
            f"instead of {field_type_input}. "
            f"Support for type objects will be removed in version 2.0.0.",
            DeprecationWarning,
            stacklevel=3,
        )
        return field_type_input.__name__
    return field_type_input


def _build_field_definition(
    field_type_str: str, allowed_values: list[str] | None
) -> tuple[Any, Any]:
    """Build a complete field definition based on type and constraints."""
    is_list = field_type_str.startswith("list")

    if is_list:
        field_type = Annotated[list[Any], AfterValidator(_make_list_validator(allowed_values))]
        if allowed_values:
            return (
                field_type,
                Field(
                    ...,
                    description=f"Allowed values: {', '.join(allowed_values)}",
                    max_length=20,
                    json_schema_extra=cast(Any, {"enum_items": allowed_values}),
                ),
            )
        return (field_type, Field(..., max_length=20))

    if allowed_values:
        field_type = Annotated[str, AfterValidator(_make_str_validator(allowed_values))]
        return (
            field_type,
            Field(
                ...,
                description=f"Allowed values: {', '.join(allowed_values)}",
                max_length=200,
                json_schema_extra=cast(Any, {"enum": allowed_values}),
            ),
        )

    base_type = _TYPE_MAPPING.get(field_type_str, str)
    if base_type is str:
        return (base_type, Field(..., max_length=200))
    return (base_type, Field(...))


def create_location_model(
    obligatory_fields: list[tuple[str, str]] | list[tuple[str, Type[Any]]],
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
        A Location model class extending LocationBase with additional fields

    Examples:
        >>> # Recommended: String type names
        >>> model = create_location_model([("name", "str"), ("tags", "list")])

        >>> # Deprecated: Python type objects (supported for backward compatibility)
        >>> model = create_location_model([("name", str), ("tags", list)])
    """
    categories = categories or {}
    fields: dict[str, Any] = {}

    for field_name, field_type_input in obligatory_fields:
        field_type_str = _normalize_field_type(field_type_input)
        allowed_values = categories.get(field_name)
        fields[field_name] = _build_field_definition(field_type_str, allowed_values)

    return create_model(
        "Location",
        __base__=LocationBase,
        __module__="goodmap.data_models.location",
        **fields,
    )

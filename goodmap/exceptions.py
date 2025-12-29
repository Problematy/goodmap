"""Custom exceptions for Goodmap application."""

import logging
import uuid as uuid_lib

from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


def _sanitize_uuid(uuid: str | None) -> str:
    """Validate and sanitize UUID to prevent injection attacks."""
    if uuid is None:
        return "<unknown>"
    try:
        # Validate UUID format
        uuid_lib.UUID(uuid)
        return uuid
    except (ValueError, AttributeError, TypeError):
        logger.warning("Invalid UUID format detected", extra={"raw_uuid": repr(uuid)})
        return "<invalid-uuid>"


class GoodmapError(Exception):
    """Base exception for all Goodmap errors."""

    pass


class ValidationError(GoodmapError):
    """Base validation error."""

    pass


class LocationValidationError(ValidationError):
    """Validation error for location data with enhanced context."""

    def __init__(self, validation_error: PydanticValidationError, uuid: str | None = None):
        self.uuid = _sanitize_uuid(uuid)
        self.original_error = validation_error
        self.validation_errors = validation_error.errors()
        super().__init__(str(validation_error))

    def __str__(self):
        # Don't expose error details in string representation
        if self.uuid and self.uuid not in ("<unknown>", "<invalid-uuid>"):
            return f"Validation failed for location '{self.uuid}'"
        return "Validation failed"


class NotFoundError(GoodmapError):
    """Resource not found error."""

    def __init__(self, uuid: str, resource_type: str = "Resource"):
        self.uuid = _sanitize_uuid(uuid)
        super().__init__(f"{resource_type} with uuid '{self.uuid}' not found")


class LocationNotFoundError(NotFoundError):
    """Location with specified UUID not found."""

    def __init__(self, uuid: str):
        super().__init__(uuid, "Location")


class AlreadyExistsError(GoodmapError):
    """Resource already exists error."""

    def __init__(self, uuid: str, resource_type: str = "Resource"):
        self.uuid = _sanitize_uuid(uuid)
        super().__init__(f"{resource_type} with uuid '{self.uuid}' already exists")


class LocationAlreadyExistsError(AlreadyExistsError):
    """Location with specified UUID already exists."""

    def __init__(self, uuid: str):
        super().__init__(uuid, "Location")


class SuggestionNotFoundError(NotFoundError):
    """Suggestion with specified UUID not found."""

    def __init__(self, uuid: str):
        super().__init__(uuid, "Suggestion")


class SuggestionAlreadyExistsError(AlreadyExistsError):
    """Suggestion with specified UUID already exists."""

    def __init__(self, uuid: str):
        super().__init__(uuid, "Suggestion")


class ReportNotFoundError(NotFoundError):
    """Report with specified UUID not found."""

    def __init__(self, uuid: str):
        super().__init__(uuid, "Report")

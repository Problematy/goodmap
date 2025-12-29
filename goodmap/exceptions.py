"""Custom exceptions for Goodmap application."""

import logging
from pydantic import ValidationError as PydanticValidationError

logger = logging.getLogger(__name__)


class GoodmapError(Exception):
    """Base exception for all Goodmap errors."""

    pass


class ValidationError(GoodmapError):
    """Base validation error."""

    pass


class LocationValidationError(ValidationError):
    """Validation error for location data with enhanced context."""

    def __init__(self, validation_error: PydanticValidationError, uuid: str | None = None):
        self.uuid = uuid
        self.original_error = validation_error
        self.validation_errors = validation_error.errors()
        super().__init__(str(validation_error))

    def __str__(self):
        uuid_context = f" for location uuid='{self.uuid}'" if self.uuid else ""
        return f"Validation failed{uuid_context}:\n{self.original_error}"


class NotFoundError(GoodmapError):
    """Resource not found error."""

    pass


class LocationNotFoundError(NotFoundError):
    """Location with specified UUID not found."""

    def __init__(self, uuid: str):
        self.uuid = uuid
        logger.warning(
            "Location not found",
            extra={
                "event": "location_not_found",
                "uuid": uuid,
            },
        )
        super().__init__(f"Location with uuid '{uuid}' not found")


class AlreadyExistsError(GoodmapError):
    """Resource already exists error."""

    pass


class LocationAlreadyExistsError(AlreadyExistsError):
    """Location with specified UUID already exists."""

    def __init__(self, uuid: str):
        self.uuid = uuid
        logger.warning(
            "Location already exists",
            extra={
                "event": "location_already_exists",
                "uuid": uuid,
            },
        )
        super().__init__(f"Location with uuid '{uuid}' already exists")

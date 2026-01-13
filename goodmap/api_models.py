"""Pydantic models for API request/response validation.

This module defines request and response models for the Goodmap REST API.
These models are used by Spectree for automatic OpenAPI schema generation
and request/response validation.
"""

from typing import Literal

from pydantic import BaseModel, Field


class LocationReportRequest(BaseModel):
    """Request model for reporting a location issue."""

    id: str = Field(..., description="Location UUID to report")
    description: str = Field(..., min_length=1, description="Description of the problem")


class LocationReportResponse(BaseModel):
    """Response model for location report submission."""

    message: str = Field(..., description="Success message")


class SuggestionStatusRequest(BaseModel):
    """Request model for updating suggestion status."""

    status: Literal["accepted", "rejected"] = Field(
        ..., description="Status to set for the suggestion"
    )


class ReportUpdateRequest(BaseModel):
    """Request model for updating a report's status and priority."""

    status: Literal["resolved", "rejected"] | None = Field(
        None, description="New status for the report"
    )
    priority: Literal["critical", "high", "medium", "low"] | None = Field(
        None, description="New priority for the report"
    )


class VersionResponse(BaseModel):
    """Response model for version endpoint."""

    backend: str = Field(..., description="Backend version")


class CSRFTokenResponse(BaseModel):
    """Response model for CSRF token endpoint (deprecated)."""

    csrf_token: str = Field(..., description="CSRF token")


class PaginationParams(BaseModel):
    """Common pagination and filtering parameters."""

    page: int | None = Field(None, ge=1, description="Page number (1-indexed)")
    per_page: int | None = Field(None, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(None, description="Field to sort by")
    sort_order: Literal["asc", "desc"] | None = Field(None, description="Sort direction")


class ClusteringParams(BaseModel):
    """Parameters for clustering request."""

    zoom: int = Field(7, ge=0, le=16, description="Map zoom level for clustering")


class ErrorResponse(BaseModel):
    """Standard error response."""

    message: str = Field(..., description="Error message")
    error: str | None = Field(None, description="Detailed error information")


class SuccessResponse(BaseModel):
    """Standard success response."""

    message: str = Field(..., description="Success message")


class BasicLocationInfo(BaseModel):
    """Basic location information (uuid + position)."""

    uuid: str = Field(..., description="Location UUID")
    position: tuple[float, float] = Field(
        ..., description="Location coordinates as (latitude, longitude)"
    )
    remark: bool = Field(False, description="Whether location has a remark")


class ClusterInfo(BaseModel):
    """Cluster information for map display."""

    uuid: str | None = Field(None, description="Location UUID (None for multi-point clusters)")
    position: tuple[float, float] = Field(..., description="Cluster center coordinates")
    count: int = Field(..., description="Number of locations in cluster")


# Note: Full location model is dynamically created from LocationBase
# and cannot be statically defined here. API endpoints will use the
# dynamically created location_model passed to core_pages() function.

"""Pydantic models for API request/response validation.

This module defines request and response models for the Goodmap REST API.
These models are used by Spectree for automatic OpenAPI schema generation
and request/response validation.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, RootModel
from spectree import BaseFile

from goodmap.data_models.location import Latitude, Longitude


class LocationReportRequest(BaseModel):
    """Request model for reporting a location issue."""

    id: str = Field(..., description="Location UUID to report")
    description: str = Field(
        ..., min_length=1, max_length=500, description="Description of the problem"
    )


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


class LocationBasicInfo(BaseModel):
    """One point as returned by the list endpoint: identity and position only."""

    uuid: str = Field(..., description="Location UUID")
    position: tuple[Latitude, Longitude] = Field(..., description="[latitude, longitude]")
    has_remark: bool = Field(
        ..., description="Whether the point has a remark, not the remark itself"
    )


class LocationList(RootModel[list[LocationBasicInfo]]):
    """List of points, each with identity and position only."""


class ClusterInfo(BaseModel):
    """One entry of the clustered list: either a single point or a cluster of them."""

    type: Literal["cluster", "point"] = Field(..., description="Which of the two this entry is")
    position: tuple[Latitude, Longitude] = Field(..., description="[latitude, longitude]")
    uuid: str | None = Field(None, description="Location UUID; null for a cluster")
    cluster_uuid: str | None = Field(
        None,
        description="Render key for a cluster, regenerated per request; null for a point",
    )
    cluster_count: int | None = Field(
        None, description="Number of points the cluster stands for; null for a point"
    )


class ClusterList(RootModel[list[ClusterInfo]]):
    """Points and clusters in one list, told apart by ``type``."""


class LocationDetail(BaseModel):
    """One point formatted for its map popup."""

    title: str = Field(..., description="The point's name")
    subtitle: str = Field(..., description="The point's type_of_place")
    position: tuple[Latitude, Longitude] = Field(..., description="[latitude, longitude]")
    data: list[tuple[str, Any]] = Field(
        ..., description="[label, value] pairs for the visible_data fields, translated"
    )
    metadata: dict[str, Any] = Field(..., description="The meta_data fields")


class CategoriesWithHelp(BaseModel):
    """Category names plus help text, returned when CATEGORIES_HELP is on."""

    categories: list[tuple[str, str]] = Field(..., description="[key, translated label] pairs")
    categories_help: list[dict[str, str]] = Field(..., description="Help text per category")


class CategoriesResponse(RootModel[CategoriesWithHelp | list[tuple[str, str]]]):
    """Bare [key, label] pairs, or an object with help text when CATEGORIES_HELP is on."""


class CategoryFull(BaseModel):
    """One category with everything needed to render its filter control."""

    key: str = Field(..., description="Query-parameter name to filter by")
    name: str = Field(..., description="Translated label")
    options: list[tuple[str, str]] = Field(..., description="[value, translated label] pairs")
    default_checked: list[str] = Field(..., description="Values checked on first load")
    filter_mode: Literal["or", "and", "exclusive", "boolean", "threshold"] = Field(
        ..., description="Which control to draw and how selections combine"
    )
    options_help: list[dict[str, str]] | None = Field(
        None, description="Present only when the CATEGORIES_HELP feature flag is on"
    )


class CategoriesFullResponse(BaseModel):
    """Every category with its options, defaults and filter mode."""

    categories: list[CategoryFull] = Field(..., description="One entry per category")
    categories_help: list[dict[str, str]] | None = Field(
        None, description="Present only when the CATEGORIES_HELP feature flag is on"
    )


class CategoryOptionsWithHelp(BaseModel):
    """A category's options plus help text, returned when CATEGORIES_HELP is on."""

    categories_options: list[tuple[str, str]] = Field(
        ..., description="[value, translated label] pairs"
    )
    categories_options_help: list[dict[str, str]] = Field(..., description="Help text per option")


class CategoryOptionsResponse(RootModel[CategoryOptionsWithHelp | list[tuple[str, str]]]):
    """Bare [value, label] pairs, or an object with help text when CATEGORIES_HELP is on."""


class LocationQueryParams(BaseModel):
    """Non-filter query parameters of the location list endpoints.

    Filter parameters are *not* listed here: they are named after the categories in the
    deployment's own data source, so they differ per instance. Call
    ``GET /api/categories-full`` to discover the ones this instance accepts.
    """

    lat: float | None = Field(None, description="Sort by distance from this latitude; requires lon")
    lon: float | None = Field(
        None, description="Sort by distance from this longitude; requires lat"
    )
    limit: int | None = Field(
        None, description="Return at most this many points, applied after sorting"
    )


class SuggestNewPointForm(BaseModel):
    """The multipart/form-data body of a new-point suggestion."""

    location: str = Field(
        ...,
        description=(
            "The whole point as one JSON object, not one form field per property. "
            "Its accepted fields come from this instance's location_obligatory_fields "
            "and categories - call GET /api/location-schema to discover them. "
            "Omit uuid; the server assigns one."
        ),
    )
    photo: BaseFile | None = Field(None, description="Optional photo, subject to ATTACHMENT limits")


class IssueType(BaseModel):
    """One reportable issue type, ready to render in a form."""

    value: str = Field(..., description="Value to send to /api/report-location")
    label: str = Field(..., description="Translated label")


class PhotoLimits(BaseModel):
    """What a photo attachment may be, from the ATTACHMENT config."""

    allowed_extensions: list[str] = Field(..., description="Permitted file extensions")
    allowed_mime_types: list[str] = Field(..., description="Permitted MIME types")
    max_size_bytes: int = Field(..., description="Largest permitted photo, in bytes")


class LocationSchemaResponse(BaseModel):
    """What this instance accepts for a new point - its schema, not a fixed contract."""

    fields: dict[str, Any] = Field(
        ...,
        description=(
            "JSON Schema property per accepted field, from the instance's location model, "
            "excluding the server-managed uuid and position"
        ),
    )
    obligatory_fields: list[Any] = Field(
        ..., description="[name, type] pairs every point must carry"
    )
    categories: dict[str, list[str]] = Field(
        ..., description="Filterable fields and their allowed values"
    )
    reported_issue_types: list[IssueType] = Field(
        ..., description="Accepted values for /api/report-location"
    )
    photo: PhotoLimits = Field(..., description="Attachment limits for the photo part")


class LanguageInfo(BaseModel):
    """One interface language."""

    name: str = Field(..., description="Language name in that language")
    flag: str = Field(..., description="Country code used to pick the flag icon")
    country: str = Field(..., description="Country code")


class LanguagesResponse(RootModel[dict[str, LanguageInfo]]):
    """Interface languages, keyed by language code."""


# Note: Full location model is dynamically created from LocationBase
# and cannot be statically defined here. API endpoints will use the
# dynamically created location_model passed to core_pages() function.

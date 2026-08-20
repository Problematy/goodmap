"""Pydantic models for API request/response validation.

This module defines request and response models for the Goodmap REST API.
These models are used by Spectree for automatic OpenAPI schema generation
and request/response validation.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field, RootModel

from goodmap.clustering import MAX_ZOOM, MIN_ZOOM
from goodmap.data_models.location import Latitude, Longitude

_POSITION_DESCRIPTION = "[latitude, longitude]"


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
    position: tuple[Latitude, Longitude] = Field(..., description=_POSITION_DESCRIPTION)


class LocationList(RootModel[list[LocationBasicInfo]]):
    """List of points, each with identity and position only."""


class LocationMarkerStyles(RootModel[dict[str, dict[str, Any]]]):
    """Map of uuid -> pin styling data: has_remark (drives the asterisk badge) plus
    whatever marker_styles.icon_field/color_field point at (drive icon/color) - for
    lazily fetching it once a marker becomes individually visible instead of getting
    it upfront for every location. Unknown/missing uuids are simply absent from the
    response, not an error."""


class MarkerStylesQueryParams(BaseModel):
    """Query parameters of the marker styles lazy-loading endpoint."""

    uuid: list[str] = Field(default_factory=list, description="Location UUIDs to fetch styling for")


def marker_style_values(location: BaseModel, style_fields: frozenset[str]) -> dict[str, Any]:
    """Pin styling data for `location`, as /api/locations/marker-styles returns it.

    Always includes has_remark (drives the asterisk badge), plus the value of any
    of `style_fields` this location actually has (drive icon/color). This is API
    response shaping, not something the location domain model needs to know how to
    do itself - it belongs alongside the models it fills, not on LocationBase.
    """
    data: dict[str, Any] = {"has_remark": bool(getattr(location, "remark", None))}
    for field in sorted(style_fields):
        value = getattr(location, field, None)
        if value is not None:
            data[field] = value
    return data


class ClusterInfo(BaseModel):
    """One entry of the clustered list: either a single point or a cluster of them."""

    type: Literal["cluster", "point"] = Field(..., description="Which of the two this entry is")
    position: tuple[Latitude, Longitude] = Field(..., description=_POSITION_DESCRIPTION)
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
    position: tuple[Latitude, Longitude] = Field(..., description=_POSITION_DESCRIPTION)
    data: list[tuple[str, Any]] = Field(
        ..., description="[label, value] pairs for the visible_data fields, translated"
    )
    metadata: dict[str, Any] = Field(..., description="The meta_data fields")


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


class LocationQueryParams(BaseModel):
    """Non-filter query parameters of the location list endpoints.

    Filter parameters are *not* listed here: they are named after the categories in the
    deployment's own data source, so they differ per instance. Call
    ``GET /api/categories-full`` to discover the ones this instance accepts.
    """

    lat: Latitude | None = Field(
        None, description="Sort by distance from this latitude; requires lon"
    )
    lon: Longitude | None = Field(
        None, description="Sort by distance from this longitude; requires lat"
    )
    limit: int | None = Field(
        None, ge=1, description="Return at most this many points, applied after sorting"
    )


class ClusteredQueryParams(LocationQueryParams):
    """Query parameters of the clustered list: the plain list's, plus ``zoom``."""

    zoom: int = Field(7, ge=MIN_ZOOM, le=MAX_ZOOM, description="Map zoom level for clustering")


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
            "excluding only the server-assigned uuid"
        ),
    )
    obligatory_fields: list[Any] = Field(
        ..., description="[name, type] pairs every point must carry"
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

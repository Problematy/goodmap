"""Validates a data source's ``initial_view`` into the view the browser opens on.

Runs once at startup (see goodmap.create_app_from_config), filling the optional
``initial_view`` config out into the complete ``{center, zoom}`` the frontend is always
handed. A data source that says nothing gets the whole of Poland, which is what the frontend
hardcoded before this was configurable.

Validation is strict and uncaught by design: a nonsensical view - a latitude of 953, a zoom
no tile layer serves - stops the app from starting, so the mistake surfaces on deploy rather
than as a map that silently opens on the wrong continent.
"""

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from goodmap.data_models.location import Latitude, Longitude

# The frontend's tile layer is OpenStreetMap and nothing configures it away, so this is the
# furthest in any goodmap map can go - Leaflet clamps the map to its tile layer's ceiling.
# Bounding the opening zoom here is what stops a config asking for a view the tiles cannot
# serve and getting a silently clamped one instead. Kept in step by hand with
# frontend/src/components/Map/map.config.js, which tells the tile layer the same number.
MAX_TILE_ZOOM = 19

# The view the frontend opened on before this was configurable: the geographic centre of
# Poland, zoomed out far enough to hold the country.
DEFAULT_CENTER = (51.917, 19.013)
DEFAULT_ZOOM = 7


class InitialView(BaseModel):
    """Where the map opens, as declared by a data source.

    ``zoom`` is a Leaflet level - roughly 6 a country, 10 a province, 13 a town, 16 a street.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    center: tuple[Latitude, Longitude] = DEFAULT_CENTER
    zoom: int = Field(default=DEFAULT_ZOOM, ge=0, le=MAX_TILE_ZOOM)


def resolve_initial_view(initial_view: Mapping[str, Any] | None) -> dict[str, Any]:
    """The opening view the frontend needs, with every field filled in.

    Args:
        initial_view: The raw ``initial_view`` config. May be empty or None - declaring one
            is optional.

    Returns:
        ``{"center": [lat, lng], "zoom": int}``, always complete, so the frontend carries no
        defaults of its own. ``center`` is a list rather than a tuple because it is headed
        for JSON either way.

    Raises:
        pydantic.ValidationError: A value is out of range or a key is unknown. Uncaught by
            design - see the module docstring.
    """
    view = InitialView.model_validate(dict(initial_view or {}))
    return {"center": list(view.center), "zoom": view.zoom}

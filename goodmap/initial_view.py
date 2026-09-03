"""Validates the configured ``initial_view`` into the view the browser opens on.

Runs once at app startup (see goodmap.create_app_from_config), turning the optional
``initial_view`` section of a data source into the complete ``{center, zoom, max_zoom}``
window.INITIAL_VIEW is always given. A data source that says nothing gets the whole of
Poland, which is what the frontend hardcoded before this was configurable.

Validation is deliberately strict and uncaught: a nonsensical view (a latitude of 953, a
``zoom`` past ``max_zoom``) stops the app from starting, the same way an unknown icon
provider does, so the mistake surfaces on deploy rather than as a map that silently opens
on the wrong continent.
"""

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field, model_validator

from goodmap.data_models.location import Latitude, Longitude

# Leaflet's own ceiling for a tile layer; no provider serves past it.
MAX_SUPPORTED_ZOOM = 25

# The view the frontend opened on before this was configurable: the geographic centre of
# Poland, zoomed out far enough to hold the country.
DEFAULT_CENTER = (51.917, 19.013)
DEFAULT_ZOOM = 7
DEFAULT_MAX_ZOOM = 19


class InitialView(BaseModel):
    """The map's opening position, as declared by a data source.

    Attributes:
        center: (latitude, longitude) the map is centred on when it loads.
        zoom: Leaflet zoom level the map opens at - roughly, 6 a country, 10 a province,
            13 a town, 16 a street.
        max_zoom: Furthest the tile layer will let a visitor zoom in.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    center: tuple[Latitude, Longitude] = DEFAULT_CENTER
    zoom: int = Field(default=DEFAULT_ZOOM, ge=0, le=MAX_SUPPORTED_ZOOM)
    max_zoom: int = Field(default=DEFAULT_MAX_ZOOM, ge=1, le=MAX_SUPPORTED_ZOOM)

    @model_validator(mode="after")
    def check_zoom_within_max(self) -> "InitialView":
        """Reject an opening zoom the tile layer would immediately clamp.

        Leaflet does not error on ``zoom > max_zoom``; it just opens somewhere other than
        where the config asked for, which is far harder to diagnose than a failed start.
        """
        if self.zoom > self.max_zoom:
            raise ValueError(
                f"zoom ({self.zoom}) cannot be greater than max_zoom ({self.max_zoom})"
            )
        return self


def resolve_initial_view(initial_view: Mapping[str, Any] | None) -> dict[str, Any]:
    """The opening view the frontend needs, with every field filled in.

    Args:
        initial_view: Raw ``initial_view`` config as returned by
            goodmap.db.get_initial_view(). May be empty or None - a data source is not
            required to declare one.

    Returns:
        ``{"center": [lat, lng], "zoom": int, "max_zoom": int}``, always complete, so the
        frontend never has to carry defaults of its own. ``center`` is a list rather than
        a tuple because it is headed for JSON either way.

    Raises:
        pydantic.ValidationError: The declared view is out of range, internally
            inconsistent, or carries an unknown key. Uncaught by design - see the module
            docstring.
    """
    view = InitialView.model_validate(dict(initial_view or {}))
    return {"center": list(view.center), "zoom": view.zoom, "max_zoom": view.max_zoom}

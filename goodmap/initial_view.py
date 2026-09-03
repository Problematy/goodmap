"""Validates a data source's ``initial_view`` into the view the browser opens on.

Runs once at startup (see goodmap.create_app_from_config), filling the optional
``initial_view`` config out into the complete ``{center, zoom, max_zoom}`` the frontend is
always handed. A data source that says nothing gets the whole of Poland, which is what the
frontend hardcoded before this was configurable.

Validation is strict and uncaught by design: a nonsensical view — a latitude of 953, a
``zoom`` past ``max_zoom`` — stops the app from starting, so the mistake surfaces on deploy
rather than as a map that silently opens on the wrong continent.
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

    ``zoom`` is a Leaflet level — roughly 6 a country, 10 a province, 13 a town, 16 a
    street — and ``max_zoom`` is as far in as the tile layer lets a visitor go.
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

    Takes the raw config, which may be empty or None since declaring a view is optional,
    and returns ``{"center": [lat, lng], "zoom": int, "max_zoom": int}`` — always complete,
    so the frontend carries no defaults of its own. ``center`` is a list rather than a tuple
    because it is headed for JSON either way.

    Raises ``pydantic.ValidationError`` for a view that is out of range, internally
    inconsistent, or carries an unknown key; uncaught by design, see the module docstring.
    """
    view = InitialView.model_validate(dict(initial_view or {}))
    return {"center": list(view.center), "zoom": view.zoom, "max_zoom": view.max_zoom}

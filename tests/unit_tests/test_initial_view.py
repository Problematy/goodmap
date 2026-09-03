import pytest
from pydantic import ValidationError

from goodmap.initial_view import (
    DEFAULT_CENTER,
    DEFAULT_ZOOM,
    MAX_TILE_ZOOM,
    resolve_initial_view,
)


def test_a_declared_view_survives_resolution_intact():
    assert resolve_initial_view({"center": [53.37, 22.89], "zoom": 8}) == {
        "center": [53.37, 22.89],
        "zoom": 8,
    }


@pytest.mark.parametrize("nothing", [None, {}], ids=["none", "empty"])
def test_a_data_source_that_declares_no_view_gets_the_default_one(nothing):
    """initial_view is optional: a deployment that says nothing still opens somewhere
    sensible, on the view the frontend used to hardcode."""
    assert resolve_initial_view(nothing) == {
        "center": list(DEFAULT_CENTER),
        "zoom": DEFAULT_ZOOM,
    }


def test_a_partial_view_keeps_the_default_for_what_it_leaves_out():
    """Only the centre usually needs moving, so declaring it must not blank the zoom."""
    assert resolve_initial_view({"center": [53.37, 22.89]}) == {
        "center": [53.37, 22.89],
        "zoom": DEFAULT_ZOOM,
    }


def test_center_is_a_list_so_it_survives_the_trip_to_the_browser():
    """The resolved view is handed to the template and serialized with tojson, where a
    tuple and a list are indistinguishable - but the resolved dict is a public contract,
    so it is pinned as the JSON-shaped type rather than pydantic's tuple."""
    assert isinstance(resolve_initial_view({"center": [1.0, 2.0]})["center"], list)


@pytest.mark.parametrize(
    "view, reason",
    [
        ({"center": [95.0, 19.0]}, "latitude past the pole"),
        ({"center": [51.9, 200.0]}, "longitude off the globe"),
        ({"center": [51.9]}, "only one coordinate"),
        ({"zoom": -1}, "negative zoom"),
        ({"zoom": 40}, "zoom past any tile layer"),
        ({"centre": [51.9, 19.0]}, "a misspelled key"),
        ({"max_zoom": 17}, "a key goodmap does not take"),
    ],
)
def test_a_view_that_could_not_be_honoured_stops_the_app_from_starting(view, reason):
    """Leaflet would quietly clamp or ignore each of these and open somewhere other than
    where the config asked, which is far harder to diagnose than a failed boot - so
    resolution raises, the same way an unknown icon provider does."""
    with pytest.raises(ValidationError):
        resolve_initial_view(view)


def test_a_misspelled_key_is_rejected_rather_than_silently_dropped():
    """Spelled out separately from the parametrized case: this is the one failure mode a
    permissive model would turn into a map that opens on the wrong continent with nothing
    in the log."""
    with pytest.raises(ValidationError, match="centre"):
        resolve_initial_view({"centre": [53.37, 22.89], "zoom": 8})


def test_the_opening_zoom_is_bounded_by_what_the_tile_layer_serves():
    """The tile provider is hardcoded to OpenStreetMap, so its ceiling is a fixed fact
    rather than a deployment's choice. Leaflet clamps the map to the tile layer instead of
    erroring, so a view asking past it would open somewhere other than configured."""
    assert resolve_initial_view({"zoom": MAX_TILE_ZOOM})["zoom"] == MAX_TILE_ZOOM

    with pytest.raises(ValidationError):
        resolve_initial_view({"zoom": MAX_TILE_ZOOM + 1})

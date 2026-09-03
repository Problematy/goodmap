import pytest
from pydantic import ValidationError

from goodmap.initial_view import (
    DEFAULT_CENTER,
    DEFAULT_MAX_ZOOM,
    DEFAULT_ZOOM,
    resolve_initial_view,
)


def test_a_declared_view_survives_resolution_intact():
    view = {"center": [53.37, 22.89], "zoom": 8, "max_zoom": 17}

    assert resolve_initial_view(view) == {"center": [53.37, 22.89], "zoom": 8, "max_zoom": 17}


@pytest.mark.parametrize("nothing", [None, {}], ids=["none", "empty"])
def test_a_data_source_that_declares_no_view_gets_the_default_one(nothing):
    """initial_view is optional: a deployment that says nothing still opens somewhere
    sensible, on the view the frontend used to hardcode."""
    assert resolve_initial_view(nothing) == {
        "center": list(DEFAULT_CENTER),
        "zoom": DEFAULT_ZOOM,
        "max_zoom": DEFAULT_MAX_ZOOM,
    }


def test_a_partial_view_keeps_the_defaults_for_what_it_leaves_out():
    """Only the centre usually needs moving; the zooms have workable defaults, so
    declaring one field must not blank the others."""
    assert resolve_initial_view({"center": [53.37, 22.89]}) == {
        "center": [53.37, 22.89],
        "zoom": DEFAULT_ZOOM,
        "max_zoom": DEFAULT_MAX_ZOOM,
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
        ({"max_zoom": 0}, "a max_zoom that permits nothing"),
        ({"zoom": 12, "max_zoom": 10}, "opening zoom beyond max_zoom"),
        ({"centre": [51.9, 19.0]}, "a misspelled key"),
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


def test_zoom_equal_to_max_zoom_is_allowed():
    """The boundary is legitimate: opening fully zoomed in is a reasonable thing to ask
    for on a single-point map."""
    assert resolve_initial_view({"zoom": 19, "max_zoom": 19})["zoom"] == 19

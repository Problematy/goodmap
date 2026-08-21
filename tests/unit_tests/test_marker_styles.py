import copy
from unittest import mock

import pytest

from goodmap.marker_styles import resolve_marker_styles

# The literal URL the frontend's resolvePhosphorIconUrl.js builds for the same icon name
# (see frontend/tests/MarkerPopup/getTypedMarkerIcon.test.jsx). Spelled out rather than
# imported from the module under test, so the two implementations drifting apart while
# the frontend shim is still in place shows up here.
PHOSPHOR_BRIDGE_URL = (
    "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/bridge-fill.svg"
)


def test_resolves_phosphor_entry_to_cdn_url():
    styles = {"icons": {"big bridge": {"provider": "phosphor", "value": "bridge"}}}

    assert resolve_marker_styles(styles)["icons"] == {"big bridge": PHOSPHOR_BRIDGE_URL}


def test_resolves_url_provider_entry_to_its_value():
    styles = {"icons": {"container": {"provider": "url", "value": "https://e.example/c.svg"}}}

    assert resolve_marker_styles(styles)["icons"] == {"container": "https://e.example/c.svg"}


def test_passes_plain_string_entry_through_unchanged():
    styles = {"icons": {"container": "https://e.example/c.svg"}}

    assert resolve_marker_styles(styles)["icons"] == {"container": "https://e.example/c.svg"}


@pytest.mark.parametrize(
    "entry",
    [
        {"provider": "phosphorr", "value": "bridge"},
        {"provider": None, "value": "bridge"},
        {"value": "bridge"},
        {"provider": "phosphor"},
        {"provider": "phosphor", "value": ""},
        {"provider": "phosphor", "value": 7},
        "",
        7,
        None,
        ["https://e.example/c.svg"],
    ],
    ids=[
        "unknown-provider",
        "null-provider",
        "no-provider",
        "no-value",
        "empty-value",
        "non-string-value",
        "empty-string",
        "number",
        "null",
        "list",
    ],
)
def test_unresolvable_entry_is_dropped_with_a_warning_naming_it(entry):
    styles = {"icons": {"big bridge": entry}}

    with mock.patch("goodmap.marker_styles.logger") as mock_logger:
        assert resolve_marker_styles(styles)["icons"] == {}

    mock_logger.warning.assert_called_once()
    assert "big bridge" in mock_logger.warning.call_args[0][1:]


def test_one_bad_entry_does_not_drop_its_good_siblings():
    """A single typo costs that pin its icon, not every other pin's."""
    styles = {
        "icons": {
            "big bridge": {"provider": "phosphor", "value": "bridge"},
            "broken": {"provider": "nope", "value": "x"},
            "plain": "https://e.example/c.svg",
        }
    }

    assert resolve_marker_styles(styles)["icons"] == {
        "big bridge": PHOSPHOR_BRIDGE_URL,
        "plain": "https://e.example/c.svg",
    }


def test_non_object_icons_resolves_to_nothing_rather_than_reaching_the_frontend():
    with mock.patch("goodmap.marker_styles.logger") as mock_logger:
        assert resolve_marker_styles({"icons": "oops"})["icons"] == {}

    mock_logger.warning.assert_called_once()


def test_empty_marker_styles_stays_empty():
    assert resolve_marker_styles({}) == {}


def test_missing_icons_key_is_not_invented():
    assert resolve_marker_styles({"icon_field": "type_of_place"}) == {"icon_field": "type_of_place"}


def test_every_other_key_is_carried_through_untouched():
    """colors maps straight to CSS colors and never had a tagged form, so it - like the
    two field names - must survive resolution unchanged."""
    styles = {
        "icon_field": "type_of_place",
        "color_field": "speed_limit",
        "colors": {"10": "#2e7d32", "50": "#c62828"},
        "icons": {"plain": "https://e.example/c.svg"},
    }

    resolved = resolve_marker_styles(styles)

    assert resolved["icon_field"] == "type_of_place"
    assert resolved["color_field"] == "speed_limit"
    assert resolved["colors"] == {"10": "#2e7d32", "50": "#c62828"}


def test_does_not_mutate_the_config_it_was_given():
    """For the json backend this dict is the db's live in-memory config, so resolving in
    place would rewrite what the deployment has stored."""
    styles = {
        "icon_field": "type_of_place",
        "icons": {"big bridge": {"provider": "phosphor", "value": "bridge"}},
    }
    before = copy.deepcopy(styles)
    icons_before = styles["icons"]

    resolve_marker_styles(styles)

    assert styles == before
    assert styles["icons"] is icons_before

import copy
from unittest import mock

import pytest

from goodmap.marker_styles import ICON_PROVIDERS, PhosphorIconProvider, resolve_marker_styles

# The URL the frontend used to build for itself before resolution moved server-side.
# Spelled out rather than imported from the module under test, so a change to how it is
# assembled has to be made deliberately here too.
PHOSPHOR_BRIDGE_URL = (
    "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/bridge-fill.svg"
)


def test_phosphor_provider_builds_the_whole_cdn_url_from_an_icon_name():
    """Pins the provider itself, independently of the resolution plumbing around it."""
    assert PhosphorIconProvider().resolve("bridge") == PHOSPHOR_BRIDGE_URL


def test_a_provider_added_to_the_registry_is_picked_up():
    """The registry's whole point: a new provider is a class plus a dict entry, with no
    edit to the resolution path."""

    class SpriteProvider:
        def resolve(self, value):
            return f"https://sprites.example/{value}.svg"

    styles = {"icons": {"big bridge": {"provider": "sprite", "value": "bridge"}}}

    with mock.patch.dict(ICON_PROVIDERS, {"sprite": SpriteProvider()}):
        resolved = resolve_marker_styles(styles)

    assert resolved["icons"] == {"big bridge": "https://sprites.example/bridge.svg"}


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
        {"value": "bridge"},
        {"provider": "phosphor"},
        7,
        None,
    ],
    ids=["unknown-provider", "no-provider", "no-value", "number", "null"],
)
def test_malformed_entry_stops_the_app_from_starting(entry):
    """Bad marker_styles config is a deploy-time mistake, so it raises rather than
    quietly costing a pin its icon - the same stance create_location_model takes on a
    category with no allowed values."""
    with pytest.raises((KeyError, TypeError, AttributeError)):
        resolve_marker_styles({"icons": {"big bridge": entry}})


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

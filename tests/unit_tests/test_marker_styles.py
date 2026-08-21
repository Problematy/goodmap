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

    styles = {"icon_provider": "sprite", "icons": {"big bridge": "bridge"}}

    with mock.patch.dict(ICON_PROVIDERS, {"sprite": SpriteProvider()}):
        resolved = resolve_marker_styles(styles)

    assert resolved["icons"] == {"big bridge": "https://sprites.example/bridge.svg"}


def test_phosphor_provider_resolves_every_entry_in_the_table():
    styles = {
        "icon_provider": "phosphor",
        "icons": {"big bridge": "bridge", "small bridge": "footprints"},
    }

    assert resolve_marker_styles(styles)["icons"] == {
        "big bridge": PHOSPHOR_BRIDGE_URL,
        "small bridge": (
            "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/footprints-fill.svg"
        ),
    }


def test_url_provider_serves_entries_the_deployment_hosts_itself():
    styles = {"icon_provider": "url", "icons": {"container": "https://e.example/c.svg"}}

    assert resolve_marker_styles(styles)["icons"] == {"container": "https://e.example/c.svg"}


@pytest.mark.parametrize(
    "styles",
    [
        {"icon_provider": "phosphorr", "icons": {"big bridge": "bridge"}},
        {"icons": {"big bridge": "bridge"}},
        {"icon_provider": None, "icons": {"big bridge": "bridge"}},
    ],
    ids=["unknown-provider", "no-provider", "null-provider"],
)
def test_malformed_config_stops_the_app_from_starting(styles):
    """Bad marker_styles config is a deploy-time mistake, so it raises rather than
    quietly costing a pin its icon - the same stance create_location_model takes on a
    category with no allowed values."""
    with pytest.raises((KeyError, TypeError)):
        resolve_marker_styles(styles)


def test_empty_marker_styles_yields_empty_tables():
    assert resolve_marker_styles({}) == {"icons": {}, "colors": {}}


@pytest.mark.parametrize("icons", [{}, None], ids=["empty-table", "no-icons-key"])
def test_nothing_to_resolve_needs_no_provider(icons):
    """A deployment that styles pins by color alone never names an icon provider, so an
    absent or empty table must not demand one."""
    styles = {"icon_field": "type_of_place", "colors": {"10": "#2e7d32"}}
    if icons is not None:
        styles["icons"] = icons

    assert resolve_marker_styles(styles) == {"icons": {}, "colors": {"10": "#2e7d32"}}


def test_only_the_two_tables_the_frontend_reads_are_built():
    """icon_field/color_field/icon_provider decide what a pin looks like server-side;
    getTypedMarkerIcon.jsx reads only icons and colors, so nothing else is shipped."""
    styles = {
        "icon_field": "type_of_place",
        "color_field": "speed_limit",
        "colors": {"10": "#2e7d32", "50": "#c62828"},
        "icon_provider": "url",
        "icons": {"plain": "https://e.example/c.svg"},
    }

    assert resolve_marker_styles(styles) == {
        "icons": {"plain": "https://e.example/c.svg"},
        "colors": {"10": "#2e7d32", "50": "#c62828"},
    }


def test_does_not_mutate_the_config_it_was_given():
    """For the json backend this dict is the db's live in-memory config, so resolving in
    place would rewrite what the deployment has stored."""
    styles = {"icon_provider": "phosphor", "icons": {"big bridge": "bridge"}}
    before = copy.deepcopy(styles)
    icons_before = styles["icons"]

    resolve_marker_styles(styles)

    assert styles == before
    assert styles["icons"] is icons_before

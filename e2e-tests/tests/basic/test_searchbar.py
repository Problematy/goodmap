"""
Searchbar Tests

Tests the address searchbar (Autocomplete + MapAutocomplete): typing a query,
picking a Nominatim suggestion, and having the map fly to its coordinates.

Regression coverage for a bug where Nominatim's response has lat/lon as
strings (e.g. `lat: "52.7365783"`), which failed a `typeof pick.lat !==
'number'` check in MapAutocomplete's onPick handler. Every pick was silently
rejected and the map never moved.
"""

import re
from urllib.parse import parse_qs, urlparse

import pytest
from playwright.sync_api import Page, Route, expect

from tests.conftest import BASE_URL, FLY_TO_TIMEOUT, TEST_LOCATIONS

SEARCH_TERM = "Rynek Wrocław"

# Mirrors an actual Nominatim /search response: lat/lon come back as strings,
# not numbers.
FAKE_NOMINATIM_RESULT = {
    "place_id": 123456789,
    "licence": "Data © OpenStreetMap contributors, ODbL 1.0. http://osm.org/copyright",
    "osm_type": "way",
    "osm_id": 40208488,
    "lat": str(TEST_LOCATIONS["WROCLAW_MARKET_SQUARE"]["lat"]),
    "lon": str(TEST_LOCATIONS["WROCLAW_MARKET_SQUARE"]["lon"]),
    "class": "highway",
    "type": "pedestrian",
    "place_rank": 26,
    "importance": 0.4553628732032192,
    "addresstype": "road",
    "name": "Rynek",
    "display_name": "Rynek, Stare Miasto, Wrocław, województwo dolnośląskie, Polska",
    "boundingbox": ["51.1094", "51.1110", "17.0308", "17.0344"],
}


def _mock_nominatim(page: Page) -> None:
    """
    Stub the Nominatim search endpoint the searchbar hits directly.

    Only responds with a result for the exact search term used in this test;
    any other query (e.g. the empty-string fetch that fires on mount) gets an
    empty result set, so no suggestion is shown before the user types.
    """

    def handle(route: Route) -> None:
        query = parse_qs(urlparse(route.request.url).query)
        if query.get("q", [""])[0] == SEARCH_TERM:
            route.fulfill(json=[FAKE_NOMINATIM_RESULT])
        else:
            route.fulfill(json=[])

    page.route("https://nominatim.openstreetmap.org/search**", handle)


class TestSearchbar:
    """Test suite for the address searchbar"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Mock Nominatim and navigate to the home page before each test."""
        _mock_nominatim(page)
        page.goto(BASE_URL, wait_until="domcontentloaded")
        return

    def test_should_fly_to_picked_suggestion_coordinates(self, page: Page):
        """
        Verify typing a query, picking the resulting suggestion, moves the
        map to that suggestion's coordinates.
        """
        location = TEST_LOCATIONS["WROCLAW_MARKET_SQUARE"]

        search_input = page.get_by_placeholder("Search address")
        search_input.fill(SEARCH_TERM)

        suggestion = page.get_by_text(FAKE_NOMINATIM_RESULT["display_name"])
        expect(suggestion).to_be_visible(timeout=5000)
        suggestion.click()

        # Leaflet only requests tiles at the final location once flyTo
        # completes, so waiting for the destination tile implicitly
        # synchronises on the animation end and confirms the map actually
        # moved (the map's default position is zoom 7, well outside this
        # pattern's 13-16 range, so this can't pass by coincidence).
        map_tile = page.locator(".leaflet-tile-container > img").first
        expect(map_tile).to_have_attribute(
            "src", re.compile(location["tile_pattern"]), timeout=FLY_TO_TIMEOUT
        )

        # The picked suggestion's text should now fill the search input.
        expect(search_input).to_have_value(FAKE_NOMINATIM_RESULT["display_name"])

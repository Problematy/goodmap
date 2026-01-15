"""
Go To My Location Button Tests

Tests the "go to my location" button functionality with geolocation mocking.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL, MARKER_LOAD_TIMEOUT, TEST_LOCATIONS


class TestGoToMyLocationButton:
    """Test suite for geolocation functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page, geolocation):
        """Setup geolocation and navigate to home page before each test"""
        # Set fake location to Rysy Mountain
        location = TEST_LOCATIONS["RYSY_MOUNTAIN"]
        geolocation(location["lat"], location["lon"])

        # Navigate to the page
        page.goto(BASE_URL, wait_until="domcontentloaded")
        return

    def test_should_click_go_to_my_location_button_and_move_map(self, page: Page):
        """
        Verify clicking the "go to my location" button moves the map
        to the user's location and loads the correct map tiles.
        """
        location = TEST_LOCATIONS["RYSY_MOUNTAIN"]

        # Click the "My Location" button
        my_location_button = page.locator(
            '.MuiButtonBase-root > [data-testid="MyLocationIcon"] > path'
        )
        my_location_button.click()

        # Wait for map tile to load and verify it's a high-zoom tile for the location
        # Different frontend versions may zoom to slightly different levels (14-16)
        map_tile = page.locator(".leaflet-tile-container > img").first
        expect(map_tile).to_have_attribute(
            "src", re.compile(location["tile_pattern"]), timeout=MARKER_LOAD_TIMEOUT
        )

"""
Accessibility Table Tests

Tests the accessibility table view functionality including:
- Table display after clicking list view button
- Correct number of rows
- Content verification
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL, MARKER_LOAD_TIMEOUT, TABLE_LOAD_TIMEOUT, TEST_LOCATIONS


class TestAccessibilityTable:
    """Test suite for accessibility table view"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page, geolocation):
        """Setup geolocation and navigate to table view before each test"""
        # Set fake location to Wroclaw Center
        location = TEST_LOCATIONS["WROCLAW_CENTER"]
        geolocation(location["lat"], location["lon"])

        # Navigate to the page
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Wait for map markers to load before clicking list view button
        markers = page.locator(".leaflet-marker-icon")
        expect(markers.first).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)

        # Click list view button
        list_view_button = page.locator('button[id="listViewButton"]')
        expect(list_view_button).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)
        list_view_button.click()

        # Wait for table to appear
        table = page.locator("table")
        expect(table).to_be_visible(timeout=TABLE_LOAD_TIMEOUT)

        return

    def test_should_properly_display_places(self, page: Page):
        """
        Verify table displays correct number of rows.
        Should have 1 header row + 2 data rows = 3 total rows.
        """
        rows = page.locator("tr")
        expect(rows).to_have_count(3)

    def test_zwierzyniecka_should_be_first_row(self, page: Page):
        """
        Verify 'Zwierzyniecka' appears in the first data row (index 1).
        """
        # Get second row (index 1) - first data row after header
        first_data_row = page.locator("tr").nth(1)
        cells = first_data_row.locator("td")

        # Verify at least one cell contains 'Zwierzyniecka'
        expect(cells.locator("text=Zwierzyniecka")).to_be_visible()

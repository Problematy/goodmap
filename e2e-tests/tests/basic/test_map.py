"""
Map Tests

Tests basic map functionality including filter list and layout.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL


class TestMap:
    """Test suite for map functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to home page before each test"""
        page.goto(BASE_URL, wait_until="domcontentloaded")
        return

    def test_displays_filter_list_with_two_categories_with_5_items(self, page: Page):
        """Verify filter list has correct number of checkboxes and category groups"""
        # Check number of checkboxes (5 filter options)
        checkboxes = page.get_by_role("checkbox")
        expect(checkboxes).to_have_count(5)

        # Check that both category groups are present
        expect(page.get_by_text("accessible_by")).to_be_visible()
        expect(page.get_by_text("type_of_place")).to_be_visible()

    def test_should_not_have_scrollbars(self, page: Page):
        """Verify the page has no horizontal or vertical scrollbars"""
        # Get viewport and document dimensions
        dimensions = page.evaluate(
            """
            () => {
                return {
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    scrollWidth: document.documentElement.scrollWidth,
                    scrollHeight: document.documentElement.scrollHeight
                };
            }
        """
        )

        # Assert no scrollbars (scroll dimensions should not exceed viewport)
        assert (
            dimensions["scrollWidth"] <= dimensions["innerWidth"]
        ), f"Horizontal scrollbar detected: scrollWidth={dimensions['scrollWidth']}, innerWidth={dimensions['innerWidth']}"

        assert (
            dimensions["scrollHeight"] <= dimensions["innerHeight"]
        ), f"Vertical scrollbar detected: scrollHeight={dimensions['scrollHeight']}, innerHeight={dimensions['innerHeight']}"

    def test_filter_checkbox_filters_markers(self, page: Page):
        """Verify clicking filter checkbox actually filters the markers on the map"""
        # Wait for markers to load
        first_marker = page.locator(".leaflet-marker-icon").first
        expect(first_marker).to_be_visible(timeout=5000)

        # Click marker cluster to expand it
        first_marker.click()

        # Wait for markers to expand - should be 2 markers after expansion
        markers = page.locator(".leaflet-marker-icon")
        expect(markers).to_have_count(2)

        # On desktop, filter panel is already visible (no toggle needed)

        # Check the "cars" filter checkbox - this should filter to only show
        # places accessible by cars (1 marker instead of 2)
        cars_checkbox = page.get_by_role("checkbox", name="cars", exact=False)
        cars_checkbox.click()

        # After filtering, only 1 marker should be visible (the one accessible by cars)
        expect(markers).to_have_count(1)

        # Uncheck to restore all markers
        cars_checkbox.click()

        # Both markers should be visible again
        expect(markers).to_have_count(2)

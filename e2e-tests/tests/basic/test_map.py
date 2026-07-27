"""
Map Tests

Tests basic map functionality including filter list and layout.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL, SEEDED_LOCATION_COUNT, TABLE_LOAD_TIMEOUT, TEST_LOCATIONS


class TestMap:
    """Test suite for map functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page, geolocation):
        """Navigate to home page before each test.

        Also grants geolocation (set to WROCLAW_CENTER), since several tests
        below use the List View table to verify filter results - it's a
        clustering-independent read of exactly what's currently filtered in,
        unlike counting `.leaflet-marker-icon` elements on the map, which
        depends on Leaflet.markercluster's zoom-dependent grouping and isn't a
        reliable way to assert result counts once bridges are spread across
        realistic real-world distances (a single cluster can require multiple
        zoom-in clicks to fully expand, rather than one click).
        """
        location = TEST_LOCATIONS["WROCLAW_CENTER"]
        geolocation(location["lat"], location["lon"])
        page.goto(BASE_URL, wait_until="domcontentloaded")
        return

    def _open_list_view(self, page: Page):
        """Switch to List View and return the results table locator."""
        list_view_button = page.locator('button[id="listViewButton"]')
        expect(list_view_button).to_be_visible(timeout=5000)
        list_view_button.click()

        table = page.locator("table")
        expect(table).to_be_visible(timeout=TABLE_LOAD_TIMEOUT)
        return table

    def test_displays_filter_list_with_four_categories(self, page: Page):
        """Verify filter list has correct number of checkboxes/radios and category groups"""
        # accessible_by (3) + type_of_place (2) + amenities (3, "and" mode is
        # still multi-select) = 8 "or"/"and" checkboxes, plus is_free
        # ("boolean") contributes 1 more checkbox (only its "true" option is
        # rendered; "false" is hidden - see FiltersForm.jsx).
        checkboxes = page.get_by_role("checkbox")
        expect(checkboxes).to_have_count(9)

        # speed_limit ("threshold") is single-select, rendered as radios.
        radios = page.get_by_role("radio")
        expect(radios).to_have_count(3)

        # Check that all category groups are present (using translated names).
        # is_free doesn't get its own header - it's grouped into "Others"
        # (see FiltersForm.jsx), labeled with its own translated name.
        expect(page.get_by_text("accessible by")).to_be_visible()
        expect(page.get_by_text("type of place")).to_be_visible()
        expect(page.get_by_text("speed limit")).to_be_visible()
        expect(page.get_by_text("Others")).to_be_visible()
        expect(page.get_by_text("Free only")).to_be_visible()

        # Every category shows a small mode badge (a single character, with a
        # tooltip on hover/focus explaining what it means) next to its title -
        # or:+, and:&, threshold:≤, boolean:• - so "or" and "and" (both
        # checkboxes, otherwise visually identical) are as distinguishable as
        # exclusive/threshold already are via their radio shape.
        expect(page.get_by_text("amenities")).to_be_visible()

        def mode_badge(symbol):
            return page.get_by_label("Help:", exact=False).filter(has_text=symbol)

        expect(mode_badge("+")).to_have_count(2)  # accessible_by, type_of_place
        expect(mode_badge("&")).to_have_count(1)  # amenities
        expect(mode_badge("≤")).to_have_count(1)  # speed_limit
        expect(mode_badge("•")).to_have_count(1)  # is_free

    def test_should_not_have_scrollbars(self, page: Page):
        """Verify the page has no horizontal or vertical scrollbars"""
        # Get viewport and document dimensions
        dimensions = page.evaluate("""
            () => {
                return {
                    innerWidth: window.innerWidth,
                    innerHeight: window.innerHeight,
                    scrollWidth: document.documentElement.scrollWidth,
                    scrollHeight: document.documentElement.scrollHeight
                };
            }
        """)

        # Assert no scrollbars (scroll dimensions should not exceed viewport)
        assert dimensions["scrollWidth"] <= dimensions["innerWidth"], (
            f"Horizontal scrollbar detected: "
            f"scrollWidth={dimensions['scrollWidth']}, "
            f"innerWidth={dimensions['innerWidth']}"
        )

        assert dimensions["scrollHeight"] <= dimensions["innerHeight"], (
            f"Vertical scrollbar detected: "
            f"scrollHeight={dimensions['scrollHeight']}, "
            f"innerHeight={dimensions['innerHeight']}"
        )

    def test_filter_checkbox_filters_markers(self, page: Page):
        """Verify clicking filter checkbox actually filters the results"""
        # "accessible_by: cars" is checked by default (see categories_default_checked
        # in the test data), so start by clearing it to see all ten seeded locations.
        cars_checkbox = page.get_by_role("checkbox", name="cars", exact=False)
        expect(cars_checkbox).to_be_checked()
        cars_checkbox.click()

        table = self._open_list_view(page)
        rows = table.locator("tr")
        # 1 header + all seeded locations
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

        # Re-check the "cars" filter checkbox - this should filter to only show
        # the 6 bridges accessible by cars (1 header + 6 data rows)
        cars_checkbox.click()
        expect(rows).to_have_count(7)

        # Uncheck to restore all results
        cars_checkbox.click()
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

    def test_or_filter_within_category_broadens_results(self, page: Page):
        """Selecting multiple checkboxes within one category (accessible_by) should
        return the union of matches (OR semantics), not only bridges that satisfy
        every selected option at once (which would incorrectly return nothing here,
        since no bridge allows both bikes and cars)."""
        cars_checkbox = page.get_by_role("checkbox", name="cars", exact=False)
        expect(cars_checkbox).to_be_checked()
        cars_checkbox.click()

        bikes_checkbox = page.get_by_role("checkbox", name="bikes", exact=False)

        table = self._open_list_view(page)
        rows = table.locator("tr")
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

        # bikes alone -> only Zwierzyniecka (1 header + 1 data row)
        bikes_checkbox.click()
        expect(rows).to_have_count(2)

        # bikes OR cars -> union of both (1 + 6, no overlap since no bridge
        # allows both bikes and cars): 1 header + 7 data rows
        cars_checkbox.click()
        expect(rows).to_have_count(8)

    def test_is_free_boolean_filter_toggles_free_only(self, page: Page):
        """is_free is a "boolean" filter: a single checkbox for "free only".
        Unchecked shows both free and paid bridges (drivers care about "free"
        or "all", not "paid only", so there's no separate option for that);
        checking it narrows down to free bridges."""
        cars_checkbox = page.get_by_role("checkbox", name="cars", exact=False)
        cars_checkbox.click()

        free_checkbox = page.get_by_role("checkbox", name="Free only", exact=False)
        expect(free_checkbox).not_to_be_checked()

        table = self._open_list_view(page)
        rows = table.locator("tr")
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

        free_checkbox.click()
        expect(free_checkbox).to_be_checked()
        # 1 header + 8 free bridges
        expect(rows).to_have_count(9)

        # Unchecking goes back to showing both free and paid bridges.
        free_checkbox.click()
        expect(free_checkbox).not_to_be_checked()
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

    def test_speed_limit_threshold_filter_includes_lower_values(self, page: Page):
        """Selecting a speed limit should also match bridges with a lower limit
        (cumulative/threshold semantics), not only an exact match. speed_limit is
        single-select (radio), since picking "30" already implies "30 or lower"."""
        cars_checkbox = page.get_by_role("checkbox", name="cars", exact=False)
        cars_checkbox.click()

        speed_30_radio = page.get_by_role("radio", name="30 km/h", exact=False)

        table = self._open_list_view(page)
        rows = table.locator("tr")
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

        # 30 km/h also matches the three 10 km/h bridges, but not the 50 km/h
        # ones: 1 header + 6 data rows
        speed_30_radio.click()
        expect(rows).to_have_count(7)

    def test_and_filter_within_category_narrows_results(self, page: Page):
        """Selecting multiple checkboxes within an "and" category (amenities)
        should narrow results to locations that have every selected value,
        the opposite of the default "or" behavior."""
        cars_checkbox = page.get_by_role("checkbox", name="cars", exact=False)
        expect(cars_checkbox).to_be_checked()
        cars_checkbox.click()

        lighting_checkbox = page.get_by_role("checkbox", name="lighting", exact=False)
        benches_checkbox = page.get_by_role("checkbox", name="benches", exact=False)

        table = self._open_list_view(page)
        rows = table.locator("tr")
        expect(rows).to_have_count(SEEDED_LOCATION_COUNT + 1)

        # lighting alone -> 8 bridges (1 header + 8 data rows)
        lighting_checkbox.click()
        expect(rows).to_have_count(9)

        # lighting AND benches -> only bridges with both (4), fewer than
        # either alone (8 and 5) - the opposite of OR's broadening.
        benches_checkbox.click()
        expect(rows).to_have_count(5)

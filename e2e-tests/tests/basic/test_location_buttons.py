"""
Location Buttons Tests

Tests the location-dependent buttons (LocationControl, SuggestNewPointButton, ListView)
tooltip behavior and disabled state when geolocation is not granted.
Also tests that geolocation permission is requested on page load.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import ALL_MOBILE_DEVICES, BASE_URL


class TestGeolocationRequestOnPageLoad:
    """Test suite verifying geolocation behavior on page load"""

    def test_page_loads_with_location_button_visible(self, page: Page):
        """
        Verify that the page loads correctly and the location button is visible.
        The new frontend only requests geolocation if permission is already granted.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # The location button should be visible
        location_button = page.locator('[aria-label*="Location target"]')
        expect(location_button).to_be_visible(timeout=5000)

    def test_buttons_respond_to_granted_permission_on_load(self, page: Page, geolocation):
        """
        Verify that when geolocation is pre-granted, buttons become active on page load.
        This confirms the automatic geolocation request works correctly.
        """
        # Grant geolocation permission and set location BEFORE navigating
        geolocation(51.10655, 17.0555)  # Wroclaw

        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Verify buttons are active (not grayed out) - use explicit wait with timeout
        location_button = page.locator('[aria-label*="Location target"]')
        expect(location_button).to_have_css("opacity", "1", timeout=5000)
        expect(location_button).to_have_css("filter", "none")

    def test_buttons_show_disabled_when_permission_denied_on_load(self, browser, webpack_script):
        """
        Verify that when geolocation permission is denied/not granted,
        buttons show disabled state on page load.
        """
        from tests.conftest import WEBPACK_SCRIPT_URL

        # Mock geolocation API to simulate permission denied - add at context level
        # so it runs before any page script
        geolocation_denied_script = """
            // Override geolocation to simulate denied permission
            Object.defineProperty(navigator, 'geolocation', {
                value: {
                    getCurrentPosition: function(success, error) {
                        // Simulate permission denied error
                        if (error) {
                            error({
                                code: 1,  // PERMISSION_DENIED
                                message: 'User denied geolocation'
                            });
                        }
                    },
                    watchPosition: function() { return 0; },
                    clearWatch: function() {}
                },
                writable: false
            });
        """

        # Create context with the geolocation denial script
        context = browser.new_context()
        context.add_init_script(geolocation_denied_script)

        page = context.new_page()

        # Setup webpack route interception
        def handle_webpack_route(route):
            route.fulfill(
                status=200,
                content_type="application/javascript; charset=utf-8",
                body=webpack_script,
            )

        def block_hmr_route(route):
            route.abort()

        page.route(WEBPACK_SCRIPT_URL, handle_webpack_route)
        page.route("**/ws", block_hmr_route)
        page.route("**/*.hot-update.*", block_hmr_route)

        try:
            page.goto(BASE_URL, wait_until="domcontentloaded")

            # Verify buttons are disabled (grayed out) - use explicit wait with timeout
            location_button = page.locator('[aria-label*="Location target"]')
            expect(location_button).to_have_css("opacity", "0.6", timeout=5000)
            expect(location_button).to_have_css("filter", "grayscale(1)")
        finally:
            page.close()
            context.close()


class TestLocationButtonsDesktop:
    """Test suite for location buttons on desktop"""

    def test_all_buttons_colored_when_location_granted(self, page: Page, geolocation):
        """
        Verify all location-dependent buttons become colored
        when geolocation permission is granted.
        """
        # Grant geolocation permission and set location
        geolocation(51.10655, 17.0555)  # Wroclaw

        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Check location button is not grayed out - use explicit wait with timeout
        location_button = page.locator('[aria-label*="Location target"]')
        expect(location_button).to_have_css("opacity", "1", timeout=5000)
        expect(location_button).to_have_css("filter", "none")

        # Check suggest button is not grayed out
        suggest_button = page.locator('[data-testid="suggest-new-point"]')
        expect(suggest_button).to_have_css("opacity", "1")
        expect(suggest_button).to_have_css("filter", "none")

        # Check list view button is not grayed out
        list_view_button = page.locator("#listViewButton")
        expect(list_view_button).to_have_css("opacity", "1")
        expect(list_view_button).to_have_css("filter", "none")


class TestLocationButtonsDesktopDisabledState:
    """Test suite for location buttons disabled state on desktop"""

    def test_location_button_shows_disabled_tooltip_on_hover(self, page: Page):
        """
        Verify location button shows disabled tooltip when hovering
        and geolocation is not granted.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Hover over the location button
        location_button = page.locator('[aria-label*="Location target"]')
        location_button.hover()

        # Check tooltip appears with disabled message
        tooltip = page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        expect(tooltip).to_contain_text("Location services are disabled")

    def test_suggest_button_shows_disabled_tooltip_on_hover(self, page: Page):
        """
        Verify suggest new point button shows disabled tooltip when hovering
        and geolocation is not granted.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Hover over the suggest button
        suggest_button = page.locator('[data-testid="suggest-new-point"]')
        suggest_button.hover()

        # Check tooltip appears with disabled message
        tooltip = page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        expect(tooltip).to_contain_text("Location services are disabled")

    def test_list_view_button_shows_disabled_tooltip_on_hover(self, page: Page):
        """
        Verify list view button shows disabled tooltip when hovering
        and geolocation is not granted.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Hover over the list view button
        list_view_button = page.locator("#listViewButton")
        list_view_button.hover()

        # Check tooltip appears with disabled message
        tooltip = page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        expect(tooltip).to_contain_text("Location services are disabled")

    def test_all_buttons_grayed_out_when_location_not_granted(self, page: Page):
        """
        Verify all location-dependent buttons have grayed out styling
        when geolocation is not granted.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Check location button styling
        location_button = page.locator('[aria-label*="Location target"]')
        expect(location_button).to_have_css("opacity", "0.6")
        expect(location_button).to_have_css("filter", "grayscale(1)")

        # Check suggest button styling
        suggest_button = page.locator('[data-testid="suggest-new-point"]')
        expect(suggest_button).to_have_css("opacity", "0.6")
        expect(suggest_button).to_have_css("filter", "grayscale(1)")

        # Check list view button styling
        list_view_button = page.locator("#listViewButton")
        expect(list_view_button).to_have_css("opacity", "0.6")
        expect(list_view_button).to_have_css("filter", "grayscale(1)")


class TestLocationButtonsMobile:
    """Test suite for location buttons on mobile devices"""

    @pytest.mark.parametrize("mobile_page", ALL_MOBILE_DEVICES, indirect=True)
    def test_list_view_shows_tooltip_on_tap(self, mobile_page: Page):
        """
        Verify list view button shows tooltip immediately on tap
        when geolocation is not granted (mobile).
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Tap the list view button
        list_view_button = mobile_page.locator("#listViewButton")
        list_view_button.wait_for(state="visible")
        list_view_button.click()

        # Check tooltip appears with disabled message
        tooltip = mobile_page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        expect(tooltip).to_contain_text("Location services are disabled")

    @pytest.mark.parametrize("mobile_page", ALL_MOBILE_DEVICES, indirect=True)
    def test_all_buttons_show_tooltip_on_tap(self, mobile_page: Page):
        """
        Verify all three location buttons show tooltips consistently on tap (mobile).
        Tests that enterTouchDelay=0 is working for all buttons.
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        buttons = [
            ("#listViewButton", "List View"),
            ('[aria-label*="Location target"]', "Location"),
            ('[data-testid="suggest-new-point"]', "Suggest"),
        ]

        for selector, _name in buttons:
            # Tap the button
            button = mobile_page.locator(selector)
            button.wait_for(state="visible")
            button.click()

            # Check tooltip appears
            tooltip = mobile_page.locator('[role="tooltip"]')
            expect(tooltip).to_be_visible(timeout=2000)
            expect(tooltip).to_contain_text("Location services are disabled")

            # Click elsewhere to dismiss tooltip and wait for it to disappear
            mobile_page.locator("body").click(position={"x": 10, "y": 10})
            expect(tooltip).not_to_be_visible(timeout=2000)

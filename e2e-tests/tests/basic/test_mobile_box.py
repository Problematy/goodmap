"""
Mobile Popup Tests

Tests popup functionality on mobile devices. On mobile devices, the app
uses Material-UI dialogs (MobilePopup component) to display location
information as a bottom sheet that slides up from the bottom.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import ALL_MOBILE_DEVICES, BASE_URL
from tests.helpers import EXPECTED_PLACE_ZWIERZYNIECKA, verify_popup_content, verify_problem_form


class TestPopupOnMobile:
    """Test suite for popup functionality on mobile devices"""

    @pytest.mark.parametrize("device_name", ALL_MOBILE_DEVICES)
    def test_displays_title_and_subtitle_in_popup(
        self, mobile_page: Page, mobile_window_open_stub, device_name: str
    ):
        """
        Verify Material-UI dialog displays title, subtitle, categories, and problem form
        correctly on mobile devices.

        Mobile uses MobilePopup component which renders as a Material-UI Dialog
        that slides up from the bottom like a bottom sheet.

        Tests on all mobile devices: iphone-x, iphone-6, ipad-2, samsung-s10
        """
        # Navigate to the page (device emulation already configured by mobile_page fixture)
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Click first marker to expand cluster
        # Use JavaScript click to bypass webpack overlay that may intercept clicks on CI
        first_marker = mobile_page.locator(".leaflet-marker-icon").first
        first_marker.evaluate("el => el.click()")

        # Wait for markers to appear (should be 2 after expansion)
        markers = mobile_page.locator(".leaflet-marker-icon")
        expect(markers).to_have_count(2)

        # Click the rightmost marker
        mobile_page.evaluate(
            """
            () => {
                const markers = document.querySelectorAll('.leaflet-marker-icon');
                let rightmostMarker = null;
                let maxX = -Infinity;

                markers.forEach(marker => {
                    const rect = marker.getBoundingClientRect();
                    if (rect.x > maxX) {
                        maxX = rect.x;
                        rightmostMarker = marker;
                    }
                });

                if (rightmostMarker) {
                    rightmostMarker.click();
                }
            }
        """
        )

        # On mobile, popup appears as Material-UI Dialog (bottom sheet)
        # TODO: Remove .MuiDialogContent-root selector after goodmap-frontend unifies popup behavior
        dialog_content = mobile_page.locator(".MuiDialogContent-root, .leaflet-popup-content")
        expect(dialog_content).to_be_visible(timeout=5000)

        # Verify popup content
        verify_popup_content(mobile_page, EXPECTED_PLACE_ZWIERZYNIECKA)

        # Verify problem form
        verify_problem_form(mobile_page)

        # Close the dialog using MUI IconButton
        # TODO: Remove .MuiIconButton-root selector after goodmap-frontend unifies popup behavior
        close_button = mobile_page.locator(
            '.MuiIconButton-root[aria-label="close"], .leaflet-popup-close-button'
        )
        expect(close_button).to_be_visible()
        # Use JavaScript click to bypass any overlay issues on CI
        close_button.evaluate("el => el.click()")

        # Verify dialog is closed
        expect(dialog_content).not_to_be_visible()

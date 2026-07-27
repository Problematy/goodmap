"""
Mobile Popup Tests

Tests popup functionality on mobile devices. On mobile devices, the app
uses Material-UI dialogs (MobilePopup component) to display location
information as a bottom sheet that slides up from the bottom.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import ALL_MOBILE_DEVICES, BASE_URL, open_test_popup
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

        # Isolate Zwierzyniecka's marker and click it directly, rather than
        # expanding a multi-marker cluster and guessing at its layout.
        open_test_popup(mobile_page)

        # On mobile, popup appears as Material-UI Dialog (bottom sheet)
        dialog_content = mobile_page.locator(".MuiDialogContent-root")
        expect(dialog_content).to_be_visible(timeout=5000)

        # Verify popup content
        verify_popup_content(mobile_page, EXPECTED_PLACE_ZWIERZYNIECKA)

        # Verify problem form
        verify_problem_form(mobile_page)

        # Close the dialog using MUI IconButton
        close_button = mobile_page.locator('.MuiIconButton-root[aria-label="close"]')
        expect(close_button).to_be_visible()
        # Use JavaScript click to bypass any overlay issues on CI
        close_button.evaluate("el => el.click()")

        # Verify dialog is closed
        expect(dialog_content).not_to_be_visible()

"""
Share Feature Tests

Tests the share button functionality in marker popups:
- Desktop: copies a ?locationId=<uuid> link to clipboard and shows a toast
- Mobile: triggers the Web Share API (navigator.share())
- Shared link: visiting ?locationId=<uuid> auto-opens the popup for that location
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import (
    ALL_MOBILE_DEVICES,
    BASE_URL,
    MARKER_LOAD_TIMEOUT,
    clear_all_checkboxes,
    open_zwierzyniecka_popup,
)


class TestShareOnDesktop:
    """Test suite for share button functionality on desktop"""

    def test_share_button_copies_link_to_clipboard(self, page: Page):
        """
        Verify clicking the share button copies a locationId link to clipboard
        and shows a toast notification.
        """
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Grant clipboard permissions
        page.context.grant_permissions(["clipboard-read", "clipboard-write"])

        open_zwierzyniecka_popup(page)

        # Verify popup is visible
        popup = page.locator(".leaflet-popup-content")
        expect(popup).to_be_visible()

        # Click the share button
        share_button = page.get_by_role("button", name="share")
        expect(share_button).to_be_visible()
        share_button.click()

        # Verify toast notification appears
        toast = page.get_by_role("status")
        expect(toast).to_contain_text("Link copied to clipboard")

        # Verify clipboard contains URL with ?locationId=
        clipboard_text = page.evaluate("() => navigator.clipboard.readText()")
        assert "?locationId=" in clipboard_text

    def test_shared_link_opens_popup_with_correct_content(self, page: Page):
        """
        Verify navigating to a URL with ?locationId= auto-opens the popup
        with the correct location content.

        Note: this passes because Zwierzyniecka's seeded coordinates keep it
        far enough from its nearest neighbor to render as a standalone marker
        at the zoom level GoToLocation.jsx navigates to. There is a known,
        separate app bug (see TODO in MarkerPopup.jsx) where this same flow
        silently fails to open the popup if the target happens to be clustered
        under the viewer's current filters/zoom - not exercised by this test.
        """
        page.goto(
            f"{BASE_URL}/?locationId=c8ecf476-5968-40da-ba5c-e810ad9ff203",
            wait_until="domcontentloaded",
        )

        clear_all_checkboxes(page)

        # Verify popup is visible
        popup = page.locator(".leaflet-popup-content")
        expect(popup).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)

        # Verify popup shows correct location
        title = popup.locator("h3")
        expect(title).to_have_text("Zwierzyniecka")

        subtitle = popup.locator("p").first
        expect(subtitle).to_have_text("small bridge")


class TestShareOnMobile:
    """Test suite for share button functionality on mobile devices"""

    @pytest.mark.parametrize("device_name", ALL_MOBILE_DEVICES)
    def test_share_button_triggers_native_share(self, mobile_page: Page, device_name: str):
        """
        Verify clicking the share button triggers navigator.share() on mobile.

        Tests on all mobile devices: iphone-x, iphone-6, ipad-2, samsung-s10
        """
        # Stub navigator.share() before navigating
        mobile_page.add_init_script("""
            window.__shareArgs = [];
            navigator.share = (data) => {
                window.__shareArgs.push(data);
                return Promise.resolve();
            };
        """)

        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        open_zwierzyniecka_popup(mobile_page)

        # On mobile, popup appears as Material-UI Dialog
        dialog_content = mobile_page.locator(".MuiDialogContent-root")
        expect(dialog_content).to_be_visible(timeout=5000)

        # Click the share button
        share_button = mobile_page.get_by_role("button", name="share")
        expect(share_button).to_be_visible()
        share_button.evaluate("el => el.click()")

        # Verify navigator.share() was called with correct URL data
        share_args = mobile_page.evaluate("() => window.__shareArgs")
        assert len(share_args) > 0, "navigator.share() was not called"
        assert "?locationId=" in share_args[0].get("url", "")

    @pytest.mark.parametrize("device_name", ALL_MOBILE_DEVICES)
    def test_shared_link_opens_popup_on_mobile(self, mobile_page: Page, device_name: str):
        """
        Verify navigating to a URL with ?locationId= auto-opens the popup on mobile.

        Tests on all mobile devices: iphone-x, iphone-6, ipad-2, samsung-s10
        """
        mobile_page.goto(
            f"{BASE_URL}/?locationId=c8ecf476-5968-40da-ba5c-e810ad9ff203",
            wait_until="domcontentloaded",
        )

        clear_all_checkboxes(mobile_page)

        # On mobile, popup appears as Material-UI Dialog
        dialog_content = mobile_page.locator(".MuiDialogContent-root")
        expect(dialog_content).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)

        # Verify popup shows correct location
        title = dialog_content.locator("h3")
        expect(title).to_have_text("Zwierzyniecka")

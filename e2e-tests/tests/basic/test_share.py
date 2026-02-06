"""
Share Feature Tests

Tests the share button functionality in marker popups:
- Desktop: copies a ?locationId=<uuid> link to clipboard and shows a toast
- Mobile: triggers the Web Share API (navigator.share())
- Shared link: visiting ?locationId=<uuid> auto-opens the popup for that location
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import ALL_MOBILE_DEVICES, BASE_URL, MARKER_LOAD_TIMEOUT


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

        # Click first marker to trigger cluster expansion
        first_marker = page.locator(".leaflet-marker-icon").first
        first_marker.click()

        # Wait for markers to appear (should be 2 after cluster expansion)
        markers = page.locator(".leaflet-marker-icon")
        expect(markers).to_have_count(2, timeout=MARKER_LOAD_TIMEOUT)

        # Click the rightmost marker
        page.evaluate(
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
        """
        page.goto(f"{BASE_URL}/?locationId=dattarro", wait_until="domcontentloaded")

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
        mobile_page.add_init_script(
            """
            window.__shareArgs = [];
            navigator.share = (data) => {
                window.__shareArgs.push(data);
                return Promise.resolve();
            };
        """
        )

        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Click first marker to expand cluster
        first_marker = mobile_page.locator(".leaflet-marker-icon").first
        first_marker.evaluate("el => el.click()")

        # Wait for markers to appear (should be 2 after expansion)
        markers = mobile_page.locator(".leaflet-marker-icon")
        expect(markers).to_have_count(2, timeout=MARKER_LOAD_TIMEOUT)

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
        mobile_page.goto(f"{BASE_URL}/?locationId=dattarro", wait_until="domcontentloaded")

        # On mobile, popup appears as Material-UI Dialog
        dialog_content = mobile_page.locator(".MuiDialogContent-root")
        expect(dialog_content).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)

        # Verify popup shows correct location
        title = dialog_content.locator("h3")
        expect(title).to_have_text("Zwierzyniecka")

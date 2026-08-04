"""
Suggest New Point Tests

Tests the "suggest a new point" dialog's validation and error feedback.
"""

import io

from PIL import Image
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL


def _open_suggest_new_point_dialog(page: Page):
    suggest_button = page.locator('[data-testid="suggest-new-point"]')
    expect(suggest_button).to_have_css("opacity", "1", timeout=5000)
    suggest_button.click()

    # Matched by name: #left-panel also has role="dialog".
    dialog = page.get_by_role("dialog", name="Suggest a New Point")
    expect(dialog).to_be_visible()
    return dialog


def _upload_tall_photo(page: Page) -> None:
    """
    Attaches a 200x3000px JPEG, tall enough that the dialog overflows and scrolls.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (200, 3000), "#3366ff").save(buffer, format="JPEG")

    page.locator('[data-testid="photo-of-point"]').set_input_files(
        files=[{"name": "tall-photo.jpg", "mimeType": "image/jpeg", "buffer": buffer.getvalue()}]
    )


class TestSuggestNewPointValidation:
    """Test suite for the suggest-new-point dialog's inline validation feedback"""

    def test_submitting_empty_required_fields_shows_inline_error(self, page: Page, geolocation):
        """
        Submitting with required fields empty must show a visible, in-dialog error
        and must not submit the form.
        """
        geolocation(51.10655, 17.0555)  # Wroclaw
        page.goto(BASE_URL, wait_until="domcontentloaded")

        dialog = _open_suggest_new_point_dialog(page)
        dialog.get_by_role("button", name="Submit").click()

        alert = dialog.get_by_role("alert")
        expect(alert).to_be_visible(timeout=5000)
        expect(alert).to_contain_text("Please fill in required fields")

        expect(dialog).to_be_visible()

    def test_error_banner_clears_when_dialog_is_reopened(self, page: Page, geolocation):
        """
        A validation error from a previous attempt must not persist into a fresh
        dialog session after cancel + reopen.
        """
        geolocation(51.10655, 17.0555)
        page.goto(BASE_URL, wait_until="domcontentloaded")

        dialog = _open_suggest_new_point_dialog(page)
        dialog.get_by_role("button", name="Submit").click()
        expect(dialog.get_by_role("alert")).to_be_visible(timeout=5000)

        dialog.get_by_role("button", name="Cancel").click()
        expect(dialog).not_to_be_visible()

        dialog = _open_suggest_new_point_dialog(page)
        expect(dialog.get_by_role("alert")).not_to_be_visible()

    def test_error_is_scrolled_into_view_when_dialog_content_is_tall(self, page: Page, geolocation):
        """
        When a tall photo makes the dialog scrollable and the user has scrolled down,
        submitting with required fields empty must scroll the error back into view,
        not just render it in the DOM above the current scroll position.
        """
        geolocation(51.10655, 17.0555)
        page.goto(BASE_URL, wait_until="domcontentloaded")

        dialog = _open_suggest_new_point_dialog(page)
        _upload_tall_photo(page)

        # Wait for the decoded image, not just the tag: the element reports a
        # non-final height until decoding completes, racing the scroll below.
        page.wait_for_function("""
            () => {
                const img = document.querySelector('img[alt="Selected"]');
                return img && img.complete && img.naturalHeight > 1000;
            }
        """)

        # The role="dialog" element is the scroll container itself.
        dialog.evaluate("el => { el.scrollTop = el.scrollHeight; }")
        scroll_top = dialog.evaluate("el => el.scrollTop")
        assert scroll_top > 0, "Dialog did not scroll - test setup is broken"

        dialog.get_by_role("button", name="Submit").click()

        alert = dialog.get_by_role("alert")
        expect(alert).to_contain_text("Please fill in required fields")
        # Timeout covers the smooth-scroll animation settling.
        expect(alert).to_be_in_viewport(timeout=8000)

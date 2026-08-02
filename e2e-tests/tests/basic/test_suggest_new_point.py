"""
Suggest New Point Tests

Tests the "suggest a new point" dialog's validation and error feedback,
in particular that error messages render as an inline banner inside the
dialog (rather than a toast that can end up stacked behind it - see
SuggestNewPointButton.jsx for context on why toasts alone weren't reliable
here).
"""

from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL


def _suggest_new_point_dialog(page: Page):
    # The page also has a permanently-present #left-panel with role="dialog"
    # (a Bootstrap offcanvas), so a bare get_by_role("dialog") is ambiguous.
    # This dialog's accessible name comes from aria-labelledby pointing at its
    # MUI DialogTitle, which disambiguates it.
    return page.get_by_role("dialog", name="Suggest a New Point")


def _open_suggest_new_point_dialog(page: Page):
    suggest_button = page.locator('[data-testid="suggest-new-point"]')
    expect(suggest_button).to_have_css("opacity", "1", timeout=5000)
    suggest_button.click()

    dialog = _suggest_new_point_dialog(page)
    expect(dialog).to_be_visible()
    return dialog


class TestSuggestNewPointValidation:
    """Test suite for the suggest-new-point dialog's inline validation feedback"""

    def test_submitting_empty_required_fields_shows_inline_error(self, page: Page, geolocation):
        """
        Submitting with required fields empty must show a visible, in-dialog error
        and must not submit the form. This is a regression test: the error used to
        render as a toast that got trapped behind the dialog by a CSS stacking
        context, making the failure look like the button silently did nothing.
        """
        geolocation(51.10655, 17.0555)  # Wroclaw
        page.goto(BASE_URL, wait_until="domcontentloaded")

        dialog = _open_suggest_new_point_dialog(page)
        dialog.get_by_role("button", name="Submit").click()

        # The alert must render inside the dialog's own stacking context, not just
        # be present anywhere in the DOM, or it can still be visually hidden.
        alert = dialog.get_by_role("alert")
        expect(alert).to_be_visible(timeout=5000)
        expect(alert).to_contain_text("Please fill in required fields")

        # Dialog stays open so the user can fix the fields and retry.
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

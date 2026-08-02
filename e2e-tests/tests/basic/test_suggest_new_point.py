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


def _upload_tall_photo(page: Page) -> None:
    """
    Attaches a synthetic, extremely tall JPEG (generated in-browser via canvas, so no
    fixture file is needed on disk) to the photo input.

    Rendered at the dialog's fixed width, a 200x3000px image becomes a huge block that
    guarantees the dialog's Paper overflows and needs to scroll - deterministically, and
    independent of viewport size or how many form fields happen to be configured. Kept
    to a moderate (not extreme) aspect ratio so the resulting smooth-scroll animation
    (see SuggestNewPointButton.jsx) finishes quickly rather than taking several seconds.
    """
    page.evaluate("""
        async () => {
            const canvas = document.createElement('canvas');
            canvas.width = 200;
            canvas.height = 3000;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#3366ff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8));
            const file = new File([blob], 'tall-photo.jpg', { type: 'image/jpeg' });

            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);

            const input = document.querySelector('[data-testid="photo-of-point"]');
            input.files = dataTransfer.files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    """)


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

    def test_error_is_scrolled_into_view_when_dialog_content_is_tall(self, page: Page, geolocation):
        """
        Regression test: when a tall photo pushes the dialog's Paper past the fold and
        the user has scrolled down (e.g. to inspect the photo/fields), a validation error
        appearing at the top of that same scroll area must be automatically scrolled into
        view - not just present in the DOM. Without this, the error is technically
        "visible" by CSS but sits entirely off-screen above the user's current scroll
        position, indistinguishable from the button silently doing nothing (the original
        bug this whole error-visibility effort started from).

        Note: it's the Dialog's Paper that scrolls here, not DialogContent - despite
        DialogContent having flex:1 1 auto + overflow-y:auto, it has no definite
        cross-size to shrink against (it's itself sized by its own content), so it just
        grows to fit everything; Paper is the ancestor with the actual maxHeight
        constraint, so its scrollTop is what ends up non-zero.
        """
        geolocation(51.10655, 17.0555)
        page.goto(BASE_URL, wait_until="domcontentloaded")

        dialog = _open_suggest_new_point_dialog(page)
        _upload_tall_photo(page)

        # Wait for the *decoded* image, not just the <img> tag's presence: with
        # width:100%/height:auto and no explicit dimensions, the element can report a
        # non-zero (but not-yet-final) box before the blob has actually finished
        # decoding, which would make the scrollHeight snapshot below race the layout.
        page.wait_for_function("""
            () => {
                const img = document.querySelector('img[alt="Selected"]');
                return img && img.complete && img.naturalHeight > 1000;
            }
        """)

        # `dialog` (role="dialog") resolves to the Paper element itself, not an ancestor
        # containing it - MUI renders the ARIA role directly on .MuiDialog-paper.
        dialog_paper = dialog
        dialog_paper.evaluate("el => { el.scrollTop = el.scrollHeight; }")
        # Sanity check the scroll actually moved away from the top - otherwise this test
        # would pass trivially without ever exercising the scroll-to-top behavior.
        scroll_top = dialog_paper.evaluate("el => el.scrollTop")
        assert scroll_top > 0, "Dialog paper did not actually scroll - test setup is broken"

        dialog.get_by_role("button", name="Submit").click()

        alert = dialog.get_by_role("alert")
        expect(alert).to_contain_text("Please fill in required fields")
        # Generous timeout: the scroll-to-top is animated (behavior: 'smooth'), and
        # to_be_in_viewport polls until the animation settles rather than checking once.
        expect(alert).to_be_in_viewport(timeout=8000)

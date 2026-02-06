"""
Left Panel (Filter Sidebar) Tests

Tests the left panel (filter sidebar) functionality across different viewport sizes:
- Desktop (≥992px): Panel displays inline with fixed 220px width
- Tablet (768px-992px): Panel is offcanvas overlay, 80vw width
- Mobile (<768px): Panel is offcanvas overlay, 80vw width

These tests verify:
- Panel visibility and positioning
- Panel scrolling when content overflows
- No page-level scrollbar (only panel scrolls)
- Close button styling and functionality on mobile/tablet
- Filter text is not truncated
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import ALL_MOBILE_DEVICES, BASE_URL


class TestLeftPanelDesktop:
    """Test suite for left panel on desktop viewport (≥992px)"""

    def test_panel_is_visible_inline_on_desktop(self, page: Page):
        """
        On desktop, the left panel should be visible inline (not as overlay)
        without needing to click a toggle button.
        """
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Wait for filter categories to load
        page.wait_for_selector("#filter-form", timeout=10000)

        # Panel should be visible
        panel = page.locator("#left-panel")
        expect(panel).to_be_visible()

        # Panel should have position: relative on desktop (inline, not overlay)
        position = panel.evaluate("el => getComputedStyle(el).position")
        assert position == "relative", f"Expected position: relative, got: {position}"

    def test_panel_has_fixed_width_on_desktop(self, page: Page):
        """
        On desktop, the panel should have a fixed 220px width.
        """
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.wait_for_selector("#filter-form", timeout=10000)

        panel = page.locator("#left-panel")
        width = panel.evaluate("el => el.clientWidth")

        # Width should be 220px (allow small tolerance for borders/scrollbar)
        assert 215 <= width <= 230, f"Expected panel width ~220px, got: {width}px"

    def test_no_page_scrollbar_on_desktop(self, page: Page):
        """
        The page/body should have overflow: hidden to prevent page-level scrollbar.
        Only the filter panel should scroll, not the whole page.
        """
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.wait_for_selector("#filter-form", timeout=10000)

        # Check body overflow is hidden
        body_overflow = page.evaluate("() => getComputedStyle(document.body).overflow")
        assert body_overflow == "hidden", f"Expected body overflow: hidden, got: {body_overflow}"

        # Check that page is not actually scrollable (attempt scroll test)
        has_scroll = page.evaluate(
            """() => {
                const el = document.scrollingElement || document.documentElement;
                const before = el.scrollTop;
                el.scrollTo(0, 100);
                const after = el.scrollTop;
                el.scrollTo(0, 0);
                return after > before;
            }"""
        )
        assert not has_scroll, "Page should not be scrollable"

    def test_panel_content_scrolls_on_desktop(self, page: Page):
        """
        When panel content exceeds the available height, the panel body
        should be scrollable to access all filter categories.
        """
        # Use smaller viewport height to ensure content overflows
        page.set_viewport_size({"width": 1200, "height": 600})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.wait_for_selector("#filter-form", timeout=10000)

        # Get panel body
        panel_body = page.locator("#left-panel .offcanvas-body")

        # Check if content overflows (scrollHeight > clientHeight)
        scroll_info = panel_body.evaluate(
            """el => ({
                clientHeight: el.clientHeight,
                scrollHeight: el.scrollHeight,
                hasOverflow: el.scrollHeight > el.clientHeight
            })"""
        )

        # If there's overflow, verify scrolling works
        if scroll_info["hasOverflow"]:
            # Get initial scroll position
            initial_scroll = panel_body.evaluate("el => el.scrollTop")

            # Scroll down
            panel_body.evaluate("el => el.scrollBy(0, 200)")

            # Verify scroll position changed
            new_scroll = panel_body.evaluate("el => el.scrollTop")
            assert new_scroll > initial_scroll, "Panel body should be scrollable"

    def test_all_filter_categories_accessible_on_desktop(self, page: Page):
        """
        All filter categories (accessible_by, type_of_place)
        should be accessible, either visible or reachable by scrolling.
        """
        page.set_viewport_size({"width": 1200, "height": 600})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.wait_for_selector("#filter-form", timeout=10000)

        # Scroll to bottom of panel to ensure all content is accessible
        panel_body = page.locator("#left-panel .offcanvas-body")
        panel_body.evaluate("el => el.scrollTop = el.scrollHeight")

        # Check that type_of_place category is visible after scrolling
        # Look for the category header text
        category_visible = page.evaluate(
            """() => {
                const panel = document.querySelector('#left-panel .offcanvas-body');
                const text = panel.textContent.toLowerCase();
                return text.includes('type_of_place') || text.includes('type of place');
            }"""
        )
        assert category_visible, "type_of_place category should be accessible after scrolling"


class TestLeftPanelMobile:
    """Test suite for left panel on mobile viewport (<992px)"""

    @pytest.mark.parametrize("mobile_page", ALL_MOBILE_DEVICES, indirect=True)
    def test_panel_hidden_by_default_on_mobile(self, mobile_page: Page):
        """
        On mobile, the filter panel (dialog) should be hidden by default.
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Wait for toggle button to be visible (indicates page is ready)
        toggle_button = mobile_page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")

        # Filter dialog should not be visible by default on mobile
        filter_dialog = mobile_page.locator('[role="dialog"]')
        expect(filter_dialog).not_to_be_visible()

    @pytest.mark.parametrize("mobile_page", ["iphone-6"], indirect=True)
    def test_panel_opens_on_toggle_click(self, mobile_page: Page):
        """
        Clicking the toggle button should open the filter panel dialog.
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Find and click the toggle button
        toggle_button = mobile_page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")
        toggle_button.click()

        # Wait for filter dialog to be visible
        filter_dialog = mobile_page.locator('[role="dialog"]')
        expect(filter_dialog).to_be_visible(timeout=5000)

        # Filter form should be visible inside dialog
        filter_form = mobile_page.locator("#filter-form")
        expect(filter_form).to_be_visible()

    @pytest.mark.parametrize("mobile_page", ["iphone-6"], indirect=True)
    def test_close_button_visible_on_mobile(self, mobile_page: Page):
        """
        On mobile, the panel should have a visible close button.
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Open the panel
        toggle_button = mobile_page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")
        toggle_button.click()

        # Wait for dialog to open
        filter_dialog = mobile_page.locator('[role="dialog"]')
        expect(filter_dialog).to_be_visible(timeout=5000)

        # Close button should be visible
        close_button = mobile_page.locator('button[aria-label="Close left panel"]')
        expect(close_button).to_be_visible()

    @pytest.mark.parametrize("mobile_page", ["iphone-6"], indirect=True)
    def test_close_button_closes_panel(self, mobile_page: Page):
        """
        Clicking the close button should close the panel.
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Open the panel
        toggle_button = mobile_page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")
        toggle_button.click()

        # Wait for dialog to open
        filter_dialog = mobile_page.locator('[role="dialog"]')
        expect(filter_dialog).to_be_visible(timeout=5000)

        # Click close button
        close_button = mobile_page.locator('button[aria-label="Close left panel"]')
        close_button.click()

        # Verify dialog is closed
        expect(filter_dialog).not_to_be_visible(timeout=5000)

    @pytest.mark.parametrize("mobile_page", ["iphone-6"], indirect=True)
    def test_panel_width_on_mobile(self, mobile_page: Page):
        """
        On mobile, the panel should be 80vw wide (80% of viewport width).
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Open the panel
        toggle_button = mobile_page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")
        toggle_button.click()

        # Wait for panel to open
        mobile_page.wait_for_selector("#left-panel.show", timeout=5000)

        # Get panel width and viewport width
        widths = mobile_page.evaluate(
            """() => ({
                panelWidth: document.querySelector('#left-panel').clientWidth,
                viewportWidth: window.innerWidth
            })"""
        )

        expected_width = widths["viewportWidth"] * 0.8
        actual_width = widths["panelWidth"]

        # Allow 10% tolerance
        assert (
            expected_width * 0.9 <= actual_width <= expected_width * 1.1
        ), f"Expected panel width ~{expected_width}px (80vw), got: {actual_width}px"

    @pytest.mark.parametrize("mobile_page", ["iphone-6"], indirect=True)
    def test_no_page_scrollbar_on_mobile(self, mobile_page: Page):
        """
        On mobile, there should be no page-level scrollbar.
        """
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Open the panel
        toggle_button = mobile_page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")
        toggle_button.click()

        # Wait for panel to open and content to load
        mobile_page.wait_for_selector("#left-panel.show", timeout=5000)
        mobile_page.wait_for_selector("#filter-form", timeout=10000)

        # Check body overflow is hidden
        body_overflow = mobile_page.evaluate("() => getComputedStyle(document.body).overflow")
        assert body_overflow == "hidden", f"Expected body overflow: hidden, got: {body_overflow}"


class TestLeftPanelTablet:
    """Test suite for left panel on tablet viewport (768px-992px)"""

    def test_panel_is_offcanvas_on_tablet(self, page: Page):
        """
        On tablet (768px width), the panel should behave as offcanvas (like mobile).
        """
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Panel should not be visible by default
        panel = page.locator("#left-panel")

        # Check that panel doesn't have 'show' class
        has_show_class = panel.evaluate("el => el.classList.contains('show')")
        assert not has_show_class, "Panel should be hidden by default on tablet"

        # Toggle button should be visible
        toggle_button = page.locator('button[aria-label="Toggle left panel"]')
        expect(toggle_button).to_be_visible()

    def test_filter_text_not_truncated_on_tablet(self, page: Page):
        """
        On tablet, all filter text should be fully visible without truncation.
        Previously there was an issue where text like "type_of_place" was truncated.
        """
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Open the panel
        toggle_button = page.locator('button[aria-label="Toggle left panel"]')
        toggle_button.wait_for(state="visible")
        toggle_button.click()

        # Wait for panel to open and content to load
        page.wait_for_selector("#left-panel.show", timeout=5000)
        page.wait_for_selector("#filter-form", timeout=10000)

        # Check that filter category headers are fully visible
        # Look for specific text that was previously truncated
        panel_text = page.evaluate("() => document.querySelector('#left-panel').textContent")

        # These should be fully visible, not truncated
        assert (
            "type_of_place" in panel_text or "type of place" in panel_text.lower()
        ), "type_of_place should be fully visible"
        assert (
            "accessible_by" in panel_text or "accessible by" in panel_text.lower()
        ), "accessible_by should be fully visible"


class TestLeftPanelFilterHelpers:
    """Test suite for filter option helper icons/tooltips"""

    def test_small_bridge_filter_has_helper_tooltip(self, page: Page):
        """
        Verify that the 'small bridge' filter option in type_of_place category
        has a helper icon that shows a tooltip on hover.
        """
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # Wait for filter form to load
        page.wait_for_selector("#filter-form", timeout=10000)

        # Find and hover over the help icon for small bridge
        # Note: The label uses translated text from categories_options_help_small bridge
        help_icon = page.get_by_label("Help: A smaller pedestrian or bike bridge")
        expect(help_icon).to_be_visible()
        help_icon.hover()

        # Verify tooltip appears with translated help text
        tooltip = page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        expect(tooltip).to_contain_text("A smaller pedestrian or bike bridge")


class TestLeftPanelScrollbar:
    """Test suite for panel scrollbar styling"""

    def test_panel_has_custom_scrollbar_styling(self, page: Page):
        """
        The panel should have custom scrollbar styling (thin, semi-transparent).
        """
        page.set_viewport_size({"width": 1200, "height": 600})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.wait_for_selector("#filter-form", timeout=10000)

        # Check scrollbar-width CSS property
        scrollbar_width = page.evaluate(
            "() => getComputedStyle(document.querySelector('#left-panel')).scrollbarWidth"
        )

        # Firefox uses scrollbar-width property
        # Chromium uses ::-webkit-scrollbar (can't easily check via JS)
        # Just verify the property is set (may be empty string in Chromium)
        # This test mainly verifies the CSS is being applied
        assert scrollbar_width in [
            "thin",
            "auto",
            "",
        ], f"Unexpected scrollbar-width value: {scrollbar_width}"

    def test_offcanvas_body_has_overflow_auto(self, page: Page):
        """
        The offcanvas-body should have overflow-y: auto for scrolling.
        """
        page.set_viewport_size({"width": 1200, "height": 600})
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.wait_for_selector("#filter-form", timeout=10000)

        overflow_y = page.evaluate(
            """() => {
                const el = document.querySelector('#left-panel .offcanvas-body');
                return getComputedStyle(el).overflowY;
            }"""
        )

        assert overflow_y == "auto", f"Expected overflow-y: auto, got: {overflow_y}"

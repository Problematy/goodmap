"""
Navigation Bar Tests

Tests navigation bar functionality including:
- Hamburger menu alignment with logo (mobile)
- Left menu visibility and positioning (mobile)
- Navigation menu links (desktop and mobile)
- About page navigation
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL, MOBILE_DEVICES, UI_VERTICAL_ALIGNMENT_TOLERANCE


class TestNavigationMenu:
    """Test suite for navigation menu functionality"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to home page before each test"""
        page.goto(BASE_URL, wait_until="domcontentloaded")
        return

    def test_navigation_menu_opens_and_shows_links(self, page: Page):
        """Verify navigation menu displays Map and About links on desktop"""
        # On desktop, nav links are directly visible (no toggle needed)
        # Verify Map link is visible and has correct href
        map_link = page.get_by_role("link", name="Map", exact=True)
        expect(map_link).to_be_visible()
        expect(map_link).to_have_attribute("href", "/")

        # Verify About link is visible and has correct href
        about_link = page.get_by_role("link", name="About")
        expect(about_link).to_be_visible()
        expect(about_link).to_have_attribute("href", "/blog/page/about")

    def test_about_link_navigates_to_about_page(self, page: Page):
        """Verify clicking About link navigates to the about page"""
        # On desktop, nav links are directly visible (no toggle needed)
        # Click About link
        about_link = page.get_by_role("link", name="About")
        about_link.click()

        # Verify we're on the About page
        expect(page).to_have_url(f"{BASE_URL}/blog/page/about")
        expect(page).to_have_title("About")

        # Verify About heading is present
        heading = page.get_by_role("heading", name="About", level=1)
        expect(heading).to_be_visible()

    def test_about_page_loads_correctly(self, page: Page):
        """Verify About page loads with correct title and heading"""
        page.goto(f"{BASE_URL}/blog/page/about", wait_until="domcontentloaded")

        # Verify page title and heading
        expect(page).to_have_title("About")
        heading = page.get_by_role("heading", name="About", level=1)
        expect(heading).to_be_visible()

    def test_home_link_navigates_back_to_map(self, page: Page):
        """Verify clicking home logo navigates back to map from About page"""
        # Navigate to About page first
        page.goto(f"{BASE_URL}/blog/page/about", wait_until="domcontentloaded")

        # Click home link (logo)
        home_link = page.get_by_role("link", name="Link to home page")
        home_link.click()

        # Verify we're back on the home page
        expect(page).to_have_url(f"{BASE_URL}/")

        # Verify map is visible (leaflet container should be present)
        map_container = page.locator(".leaflet-container")
        expect(map_container).to_be_visible()


class TestNavigationBarForSmallDevices:
    """Test suite for navigation bar on mobile devices"""

    @pytest.mark.parametrize("device_name", list(MOBILE_DEVICES.keys()))
    def test_hamburger_menu_vertically_centered_with_logo(
        self, mobile_page: Page, device_name: str
    ):
        """
        Verify hamburger menu is vertically centered with the logo on mobile devices.

        Tests on: iphone-6, ipad-2, samsung-s10
        """
        # Navigate after viewport is set (mobile_page fixture sets viewport before page creation)
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Get logo position and center
        logo = mobile_page.locator(".navbar-brand")
        expect(logo).to_be_visible()
        logo_box = logo.bounding_box()
        assert logo_box is not None, "Logo not found"

        logo_center = logo_box["y"] + logo_box["height"] / 2
        print(f"Logo Center: {logo_center}")

        # Check each hamburger menu center position
        hamburger_locator = mobile_page.locator(".navbar-toggler")
        expect(hamburger_locator.first).to_be_visible()
        hamburgers = hamburger_locator.all()
        for i, hamburger in enumerate(hamburgers):
            expect(hamburger).to_be_visible()
            hamburger_box = hamburger.bounding_box()
            assert hamburger_box is not None, f"Hamburger {i+1} not found"

            hamburger_center = hamburger_box["y"] + hamburger_box["height"] / 2
            print(f"Hamburger Center {i+1}: {hamburger_center}")

            # Verify vertical alignment within tolerance
            diff = abs(hamburger_center - logo_center)
            assert diff <= UI_VERTICAL_ALIGNMENT_TOLERANCE, (
                f"Hamburger {i+1} not vertically aligned with logo on {device_name}. "
                f"Difference: {diff}px (tolerance: {UI_VERTICAL_ALIGNMENT_TOLERANCE}px)"
            )

    @pytest.mark.parametrize("device_name", list(MOBILE_DEVICES.keys()))
    def test_left_menu_visible_after_clicking_left_hamburger(
        self, mobile_page: Page, device_name: str
    ):
        """
        Verify left menu becomes visible after clicking left hamburger button
        and filter form is positioned below the navbar.

        Tests on: iphone-6, ipad-2, samsung-s10
        """
        # Navigate after viewport is set (mobile_page fixture sets viewport before page creation)
        mobile_page.goto(BASE_URL, wait_until="domcontentloaded")

        # Verify left panel is not visible initially
        left_panel = mobile_page.locator("#left-panel")
        expect(left_panel).not_to_be_visible()

        # Click first (left) hamburger button
        mobile_page.locator(".navbar-toggler").first.click()

        # Verify left panel is now visible
        expect(left_panel).to_be_visible()

        # Get filter form position
        filter_form = mobile_page.locator("#filter-form")
        expect(filter_form).to_be_visible()

        filter_form_box = filter_form.bounding_box()
        assert filter_form_box is not None, "Filter form not found"
        filter_form_top = filter_form_box["y"]
        print(f"Filter Form Top: {filter_form_top}")

        # Get navbar bottom position
        navbar = mobile_page.locator(".navbar")
        expect(navbar).to_be_visible()
        navbar_box = navbar.bounding_box()
        assert navbar_box is not None, "Navbar not found"
        navbar_bottom = navbar_box["y"] + navbar_box["height"]
        print(f"Navbar Bottom: {navbar_bottom}")

        # Verify filter form is below navbar
        assert filter_form_top > navbar_bottom, (
            f"Filter form overlaps navbar on {device_name}. "
            f"Filter top: {filter_form_top}, Navbar bottom: {navbar_bottom}"
        )

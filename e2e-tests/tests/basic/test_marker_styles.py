"""
Marker Styles Tests

Tests that the map picks pin icon/color per marker_styles (icon_field:
type_of_place, color_field: speed_limit - see e2e_test_data_initial.json), and
that a location with both a remark and a marker_styles match keeps its
type/color styling with an asterisk badge overlay, rather than losing it to
the plain asterisk icon (see getTypedMarkerIcon.jsx/MarkerPopup.jsx).
"""

from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL, MARKER_LOAD_TIMEOUT, open_test_popup

# "big bridge" and "small bridge" each get their own Phosphor Icons (MIT) type
# icon - see e2e_test_data_initial.json's marker_styles.icons and
# getTypedMarkerIcon.jsx (icon URLs are CSS mask-image'd onto the pin, tinted
# by the matched color, rather than embedded as inline SVG path data).
BIG_BRIDGE_TYPE_ICON_URL = (
    "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/bridge-fill.svg"
)
SMALL_BRIDGE_TYPE_ICON_URL = (
    "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/footprints-fill.svg"
)


class TestMarkerStyles:
    """Test suite for marker_styles-driven pin icons/colors"""

    def test_fast_bridge_marker_uses_type_icon_and_red_speed_color(self, page: Page):
        """Pokoju (big bridge, speed_limit=50, no remark) is the only seeded bridge
        with all three of lighting+benches+toilets (amenities is an "and" category -
        see test_and_filter_within_category_narrows_results in test_map.py), so
        checking all three isolates its marker without relying on clustering
        distance/zoom assumptions."""
        page.goto(BASE_URL, wait_until="domcontentloaded")

        # "cars" is checked by default (Pokoju is cars-accessible); narrow further.
        for amenity in ("lighting", "benches", "toilets"):
            page.get_by_role("checkbox", name=amenity, exact=False).click()

        marker = page.locator(".custom-typed-marker-icon")
        expect(marker).to_have_count(1, timeout=MARKER_LOAD_TIMEOUT)

        # The pin shape itself (a masked div, not an inline <path>), filled with
        # speed_limit=50's color.
        pin = marker.locator(".custom-typed-marker-pin")
        expect(pin).to_have_css("background-color", "rgb(198, 40, 40)")  # #c62828
        # The type_of_place icon, configured for "big bridge" - masked onto a div
        # via CSS rather than embedded as an inline <path>.
        type_icon = marker.locator(".custom-typed-marker-type-icon")
        expect(type_icon).to_have_count(1)
        expect(type_icon).to_have_css("mask-image", f'url("{BIG_BRIDGE_TYPE_ICON_URL}")')
        # No remark on Pokoju, so no asterisk badge.
        expect(marker.locator("span")).to_have_count(0)

    def test_slow_bridge_marker_uses_type_icon_and_green_speed_color(self, page: Page):
        """Piaskowy (small bridge, speed_limit=10, no remark, toilets) is the
        only seeded speed<=10 bridge with toilets - the other two speed=10
        bridges (Zwierzyniecka, Tumski) have lighting/benches but neither has
        toilets, so combining the speed_limit=10 radio with the toilets
        checkbox isolates it without relying on clustering distance/zoom
        assumptions. "cars" is unchecked first since Piaskowy is
        pedestrians-only."""
        page.goto(BASE_URL, wait_until="domcontentloaded")

        page.get_by_role("checkbox", name="cars", exact=False).click()
        page.get_by_role("radio", name="10 km/h", exact=False).click()
        page.get_by_role("checkbox", name="toilets", exact=False).click()

        marker = page.locator(".custom-typed-marker-icon")
        expect(marker).to_have_count(1, timeout=MARKER_LOAD_TIMEOUT)

        pin = marker.locator(".custom-typed-marker-pin")
        expect(pin).to_have_css("background-color", "rgb(46, 125, 50)")  # #2e7d32 (speed_limit=10)
        type_icon = marker.locator(".custom-typed-marker-type-icon")
        expect(type_icon).to_have_count(1)
        expect(type_icon).to_have_css("mask-image", f'url("{SMALL_BRIDGE_TYPE_ICON_URL}")')
        # No remark on Piaskowy, so no asterisk badge.
        expect(marker.locator("span")).to_have_count(0)

    def test_remarked_bridge_keeps_type_and_color_styling_with_asterisk_badge(self, page: Page):
        """Zwierzyniecka has both a remark and marker_styles-matching fields
        (small bridge, speed_limit=10) - it should render its normal typed/colored
        pin plus an asterisk badge, not fall back to the plain asterisk icon
        (every type_of_place/speed_limit value happens to be covered by
        marker_styles in this seeded dataset, so that plain-icon fallback path
        isn't exercised here - it's covered at the unit level instead, see
        getTypedMarkerIcon.test.jsx's "falls back to the plain asterisk icon"
        case)."""
        page.goto(BASE_URL, wait_until="domcontentloaded")
        open_test_popup(page)

        expect(page.locator('img[alt="Marker-Asterisk"]')).to_have_count(0)

        marker = page.locator(".custom-typed-marker-icon")
        expect(marker).to_have_count(1, timeout=MARKER_LOAD_TIMEOUT)

        pin = marker.locator(".custom-typed-marker-pin")
        expect(pin).to_have_css("background-color", "rgb(46, 125, 50)")  # #2e7d32 (speed_limit=10)
        type_icon = marker.locator(".custom-typed-marker-type-icon")
        expect(type_icon).to_have_count(1)
        expect(type_icon).to_have_css("mask-image", f'url("{SMALL_BRIDGE_TYPE_ICON_URL}")')
        expect(marker.locator("span")).to_have_text("*")

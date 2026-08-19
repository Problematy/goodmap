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

# "big bridge" and "small bridge" each get their own Phosphor Icons (MIT) glyph -
# see e2e_test_data_initial.json's marker_styles.icons and getTypedMarkerIcon.jsx
# (icon URLs are CSS mask-image'd onto the pin, tinted by the matched color,
# rather than embedded as inline SVG path data).
BIG_BRIDGE_GLYPH_URL = (
    "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/bridge-fill.svg"
)
SMALL_BRIDGE_GLYPH_URL = (
    "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/footprints-fill.svg"
)


class TestMarkerStyles:
    """Test suite for marker_styles-driven pin icons/colors"""

    def test_fast_bridge_marker_uses_type_glyph_and_red_speed_color(self, page: Page):
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

        # The pin shape itself, filled with speed_limit=50's color.
        expect(marker.locator("path")).to_have_attribute("fill", "#c62828")
        # The type_of_place glyph, configured for "big bridge" - masked onto a div
        # via CSS rather than embedded as an inline <path>.
        glyph = marker.locator(".custom-typed-marker-glyph")
        expect(glyph).to_have_count(1)
        expect(glyph).to_have_css("mask-image", f'url("{BIG_BRIDGE_GLYPH_URL}")')
        # No remark on Pokoju, so no asterisk badge.
        expect(marker.locator("text")).to_have_count(0)

    # Note: a second real-browser color case (e.g. speed_limit=10 -> green) isn't
    # covered here. The only speed=10 bridge without a remark (Piaskowy) can't be
    # isolated to a standalone marker via the left panel's filters - its amenities
    # ([benches]) are a subset of a remarked neighbor's (Tumski, [lighting,
    # benches]) barely 230m away, so any filter combo that includes Piaskowy also
    # includes Tumski, and Leaflet.markercluster groups them into one cluster
    # bubble at the map's default zoom, hiding both individual markers. The
    # color-lookup logic itself (arbitrary field values, including a "10" ->
    # green case) is covered generically at the unit level in
    # frontend/tests/MarkerPopup/getTypedMarkerIcon.test.jsx.

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

        expect(marker.locator("path")).to_have_attribute("fill", "#2e7d32")  # speed_limit=10
        glyph = marker.locator(".custom-typed-marker-glyph")
        expect(glyph).to_have_count(1)
        expect(glyph).to_have_css("mask-image", f'url("{SMALL_BRIDGE_GLYPH_URL}")')
        expect(marker.locator("text")).to_have_text("*")

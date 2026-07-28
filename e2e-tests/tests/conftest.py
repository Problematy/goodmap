"""
Pytest fixtures and configuration for Playwright E2E tests.

Provides custom fixtures for:
- Webpack script caching and interception
- Window.open() stub tracking
- Geolocation mocking
- Performance tracking for stress tests
"""

import json
from collections.abc import Callable, Generator
from pathlib import Path

import pytest
from playwright.sync_api import BrowserContext, Page, expect

BASE_URL = "http://localhost:5000"

MARKER_LOAD_TIMEOUT = 5000
TABLE_LOAD_TIMEOUT = 5000
FLY_TO_TIMEOUT = 20000

# Number of bridges in e2e_test_data_initial.json's "data" array. Kept as a
# single constant so tests don't hardcode this count (and its +1-for-header
# variant) in multiple places.
SEEDED_LOCATION_COUNT = 10

MOBILE_DEVICES = {
    "iphone-x": {
        "viewport": {"width": 375, "height": 812},
        "user_agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
            "AppleWebKit/604.1.38 (KHTML, like Gecko) "
            "Version/11.0 Mobile/15A372 Safari/604.1"
        ),
    },
    "iphone-6": {
        "viewport": {"width": 375, "height": 667},
        "user_agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
            "AppleWebKit/604.1.38 (KHTML, like Gecko) "
            "Version/11.0 Mobile/15A372 Safari/604.1"
        ),
    },
    "ipad-2": {
        "viewport": {"width": 768, "height": 1024},
        "user_agent": (
            "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) "
            "AppleWebKit/604.1.34 (KHTML, like Gecko) "
            "Version/11.0 Mobile/15A5341f Safari/604.1"
        ),
    },
    "samsung-s10": {
        "viewport": {"width": 360, "height": 760},
        "user_agent": (
            "Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-G973U) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "SamsungBrowser/9.2 Chrome/67.0.3396.87 Mobile Safari/537.36"
        ),
    },
}

ALL_MOBILE_DEVICES = list(MOBILE_DEVICES.keys())

UI_VERTICAL_ALIGNMENT_TOLERANCE = 3

TEST_LOCATIONS = {
    "RYSY_MOUNTAIN": {
        "lat": 49.179,
        "lon": 20.088,
        "tile_pattern": r"https://[abc]\.tile\.openstreetmap\.org/1[3-6]/\d+/\d+\.png",
    },
    # Matches Zwierzyniecka's seeded position exactly, so it's guaranteed to
    # sort first by distance in tests that rely on that ordering.
    "WROCLAW_CENTER": {"lat": 51.108056, "lon": 17.07},
}


def clear_all_checkboxes(page: Page) -> None:
    """
    Click the "Clear filters" button to reset all selected category filters.

    Several tests rely on all seeded locations being visible, which requires
    clearing any filters checked by default (see categories_default_checked
    in the e2e test data) before asserting on marker/location counts.

    Opens the mobile filter panel (if collapsed) to reach the button, and
    closes it again afterwards so it doesn't obscure subsequent interactions.

    Clearing filters can trigger a marker refetch that mounts a location
    whose popup auto-opens (e.g. a pending ?locationId= shared link). That
    popup dialog can stack on top of the filter panel before the close button
    is clicked, so the close is dispatched via JS: it fires the same click
    event Bootstrap listens for, but skips Playwright's hit-testing, which
    would otherwise block on the overlapping dialog.
    """
    toggle_button = page.locator('button[aria-label="Toggle left panel"]')
    opened_dialog = toggle_button.is_visible()
    if opened_dialog:
        toggle_button.click()

    page.wait_for_selector("#filter-form", timeout=MARKER_LOAD_TIMEOUT)
    page.locator("#clear-filters-button").click()

    if opened_dialog:
        page.locator('button[aria-label="Close left panel"]').evaluate("el => el.click()")


def open_test_popup(page: Page) -> None:
    """
    Filter down to exactly one known seeded location (Zwierzyniecka) and
    click its marker to open its popup.

    Clicking into a multi-marker cluster spiderfies it into a layout whose
    on-screen ordering isn't guaranteed to match geographic position
    (especially on narrow mobile viewports) or to be stable as more
    locations are seeded, so tests that need a specific, known location's
    popup should isolate it first rather than reaching into an expanded
    cluster by pixel position (e.g. "rightmost marker").

    "bikes" uniquely identifies Zwierzyniecka among the seeded e2e bridges
    (the only accessible_by option no other bridge has), so checking it
    leaves exactly one marker on the map.
    """
    toggle_button = page.locator('button[aria-label="Toggle left panel"]')
    opened_dialog = toggle_button.is_visible()
    if opened_dialog:
        toggle_button.click()

    page.wait_for_selector("#filter-form", timeout=MARKER_LOAD_TIMEOUT)
    page.locator("#clear-filters-button").click()
    page.locator("#filter-form input#bikes").check()

    if opened_dialog:
        page.locator('button[aria-label="Close left panel"]').evaluate("el => el.click()")

    markers = page.locator(".leaflet-marker-icon")
    expect(markers).to_have_count(1, timeout=MARKER_LOAD_TIMEOUT)
    markers.first.click()


def _block_hmr(page: Page) -> None:
    """Block HMR/hot reload requests to prevent page refreshes during tests."""
    page.route("**/ws", lambda route: route.abort())
    page.route("**/*.hot-update.*", lambda route: route.abort())


def _stub_window_open(page: Page) -> Callable[[], list[str]]:
    """Stub window.open() and return a callable that retrieves opened URLs."""
    opened_urls = []
    page.expose_function("__captureWindowOpen", lambda url: opened_urls.append(url))
    page.add_init_script("""
        window.open = function(url, target, features) {
            window.__captureWindowOpen(url);
            return null;
        };
    """)
    return lambda: opened_urls.copy()


@pytest.fixture
def page(page: Page) -> Page:
    """
    Override the default Playwright page fixture.

    Sets desktop viewport size (1280x800) for consistent desktop testing.
    Blocks HMR/websocket requests to prevent page refreshes during tests.
    """
    page.set_viewport_size({"width": 1280, "height": 800})
    _block_hmr(page)
    return page


@pytest.fixture
def window_open_stub(page: Page) -> Callable[[], list[str]]:
    """
    Stub window.open() and track all opened URLs.

    Returns a callable that returns the list of URLs opened via window.open().
    """
    return _stub_window_open(page)


@pytest.fixture
def mobile_page(new_context, request) -> Generator[Page, None, None]:
    """
    Create a page with proper mobile device emulation.

    Creates a new browser context with the correct user agent,
    ensuring that react-device-detect properly identifies the device as mobile.

    Supports two parametrization styles:
    1. Indirect: @pytest.mark.parametrize("mobile_page", ALL_MOBILE_DEVICES, indirect=True)
    2. Legacy: @pytest.mark.parametrize("device_name", ALL_MOBILE_DEVICES)

    Uses pytest-playwright's new_context factory fixture (rather than calling
    browser.new_context() directly) so CLI-driven options like
    --video=retain-on-failure still apply, and so failures on mobile tests
    produce the same video/trace artifacts as desktop tests.
    """
    if hasattr(request, "param"):
        device_name = request.param
    else:
        callspec = getattr(request.node, "callspec", None)
        if callspec is None:
            raise ValueError("mobile_page fixture requires parametrization")
        device_name = callspec.params.get("device_name")
        if not device_name:
            raise ValueError("mobile_page fixture requires 'device_name' parameter")

    device_config = MOBILE_DEVICES[device_name]

    context = new_context(
        viewport=device_config["viewport"],
        user_agent=device_config["user_agent"],
        has_touch=True,
    )
    page = context.new_page()
    _block_hmr(page)

    yield page

    page.close()
    context.close()


@pytest.fixture
def mobile_window_open_stub(mobile_page: Page) -> Callable[[], list[str]]:
    """
    Stub window.open() for mobile pages and track all opened URLs.

    Same as window_open_stub but works with the mobile_page fixture.
    """
    return _stub_window_open(mobile_page)


@pytest.fixture
def geolocation(context: BrowserContext) -> Callable[[float, float], None]:
    """
    Provide a function to set browser geolocation.

    Returns a callable that sets the geolocation to the given lat/lon coordinates.
    """
    context.grant_permissions(["geolocation"])

    def set_location(latitude: float, longitude: float) -> None:
        context.set_geolocation({"latitude": latitude, "longitude": longitude})

    return set_location


@pytest.fixture
def performance_tracker():
    """
    Track performance metrics for stress tests.

    Returns an object with methods to add_run(), calculate_stats(), and save() results.
    """

    class PerformanceTracker:
        def __init__(self):
            self.run_times = []
            self.num_runs = 0
            self.expected_runs = 0

        def add_run(self, run_number: int, time_ms: float, markers: int):
            self.run_times.append(
                {"run": run_number, "time": round(time_ms, 2), "markers": markers}
            )
            self.num_runs += 1

        def calculate_stats(self, max_allowed_ms: int = 25000):
            if not self.run_times:
                return {}

            times = [r["time"] for r in self.run_times]
            markers = [r["markers"] for r in self.run_times]

            return {
                "numRuns": self.num_runs,
                "expectedRuns": self.expected_runs or self.num_runs,
                "runTimes": self.run_times,
                "avgTime": round(sum(times) / len(times), 2),
                "minTime": round(min(times), 2),
                "maxTime": round(max(times), 2),
                "avgMarkers": round(sum(markers) / len(markers), 2) if markers else 0,
                "maxAllowed": max_allowed_ms,
                "passed": max(times) <= max_allowed_ms,
            }

        def save(self, filepath: str, max_allowed_ms: int = 25000):
            stats = self.calculate_stats(max_allowed_ms)
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w") as f:
                json.dump(stats, f, indent=2)

    return PerformanceTracker()

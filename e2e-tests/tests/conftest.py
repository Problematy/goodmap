"""
Pytest fixtures and configuration for Playwright E2E tests.

This module provides custom fixtures for:
- Webpack script caching and interception
- Window.open() stub tracking
- Geolocation mocking
- Performance tracking for stress tests
"""

import json
from collections.abc import Callable, Generator
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

import pytest
from playwright.sync_api import BrowserContext, Page, Route

# Constants
WEBPACK_SCRIPT_URL = "http://localhost:8080/index.js"
CACHE_DIR = Path(".playwright-cache")
CACHE_FILE = CACHE_DIR / "webpack-script.js"
BASE_URL = "http://localhost:5000"

# Timeouts (in milliseconds)
MAP_LOAD_TIMEOUT = 5000
MARKER_LOAD_TIMEOUT = 5000
TABLE_LOAD_TIMEOUT = 5000

# Script to remove webpack-dev-server overlay that can intercept clicks
# Uses CSS (when head exists) + MutationObserver (aggressive removal)
WEBPACK_OVERLAY_REMOVAL_SCRIPT = """
// Inject CSS to hide overlay - append to head if exists, otherwise documentElement
const style = document.createElement('style');
style.textContent = `#webpack-dev-server-client-overlay {
    display: none !important;
    pointer-events: none !important;
    visibility: hidden !important;
}`;
(document.head || document.documentElement).appendChild(style);

// Aggressive MutationObserver - remove overlay immediately when it appears
const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
        for (const node of mutation.addedNodes) {
            if (node.id === 'webpack-dev-server-client-overlay') {
                node.remove();
                return;
            }
        }
    }
    // Also check if it already exists
    const overlay = document.getElementById('webpack-dev-server-client-overlay');
    if (overlay) overlay.remove();
});
observer.observe(document.documentElement, { childList: true, subtree: true });
"""

# Mobile device configurations for Playwright
MOBILE_DEVICES = {
    "iphone-x": {
        "viewport": {"width": 375, "height": 812},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
    },
    "iphone-6": {
        "viewport": {"width": 375, "height": 667},
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1",
    },
    "ipad-2": {
        "viewport": {"width": 768, "height": 1024},
        "user_agent": "Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1",
    },
    "samsung-s10": {
        "viewport": {"width": 360, "height": 760},
        "user_agent": "Mozilla/5.0 (Linux; Android 9; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/9.2 Chrome/67.0.3396.87 Mobile Safari/537.36",
    },
}

# Device lists for parametrized tests
ALL_MOBILE_DEVICES = list(MOBILE_DEVICES.keys())

# UI alignment tolerance (in pixels)
UI_VERTICAL_ALIGNMENT_TOLERANCE = 3

# Test locations
TEST_LOCATIONS = {
    "RYSY_MOUNTAIN": {
        "lat": 49.179,
        "lon": 20.088,
        # Tile pattern matches zoom 14-16 for Rysy Mountain area
        # Zoom 16: 36424/22456, Zoom 15: 18211-18212/11227-11228, Zoom 14: 9105-9106/5613-5614
        "tile_pattern": r"https://[abc]\.tile\.openstreetmap\.org/1[456]/\d+/\d+\.png",
    },
    "WROCLAW_CENTER": {"lat": 51.10655, "lon": 17.0555},
}


def pytest_configure(config):
    """
    Pytest hook called before test collection.
    Fetches and caches the webpack script from the frontend dev server.
    """
    # In xdist, run this only on master (workers share FS)
    if getattr(config, "workerinput", None) is not None:
        return

    # Create cache directory if it doesn't exist
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Fetch webpack script if not cached
    if not CACHE_FILE.exists():
        print(f"\nFetching webpack script from {WEBPACK_SCRIPT_URL}...")
        try:
            # Validate URL scheme and hostname (Ruff S310)
            parsed = urlparse(WEBPACK_SCRIPT_URL)
            if parsed.scheme not in {"http", "https"} or parsed.hostname not in {
                "localhost",
                "127.0.0.1",
            }:
                raise ValueError(f"Refusing non-local URL: {WEBPACK_SCRIPT_URL}")

            with urlopen(WEBPACK_SCRIPT_URL, timeout=10) as response:  # noqa: S310
                script_content = response.read().decode("utf-8")

            # Validate script content
            if len(script_content) < 100:
                raise ValueError("Webpack script content is too short, likely invalid")

            # Save to cache (atomic write via temp file)
            tmp = CACHE_FILE.with_suffix(".js.tmp")
            tmp.write_text(script_content, encoding="utf-8")
            tmp.replace(CACHE_FILE)
            print(f"Webpack script cached to {CACHE_FILE} ({len(script_content)} bytes)")

        except (URLError, TimeoutError) as e:
            print(f"WARNING: Failed to fetch webpack script: {e}")
            print("Tests may fail if webpack script is required.")
    else:
        print(f"\nUsing cached webpack script from {CACHE_FILE}")


@pytest.fixture(scope="session")
def webpack_script() -> str:
    """
    Session-scoped fixture that loads the cached webpack script.
    """
    if not CACHE_FILE.exists():
        raise FileNotFoundError(
            f"Webpack script cache file not found: {CACHE_FILE}. "
            "Ensure the frontend dev server is running on localhost:8080."
        )

    return CACHE_FILE.read_text()


@pytest.fixture
def page(page: Page, webpack_script: str) -> Page:
    """
    Override the default Playwright page fixture to intercept webpack script requests.

    This fixture automatically routes requests to the webpack script URL
    and serves the cached version instead of hitting the network.
    Sets desktop viewport size (1280x800) for consistent desktop testing.
    Blocks HMR/websocket requests to prevent page refreshes during tests.
    """
    # Set desktop viewport size
    page.set_viewport_size({"width": 1280, "height": 800})

    def handle_webpack_route(route: Route) -> None:
        """Intercept webpack script requests and serve from cache"""
        route.fulfill(
            status=200, content_type="application/javascript; charset=utf-8", body=webpack_script
        )

    def block_hmr_route(route: Route) -> None:
        """Block HMR/hot reload requests to prevent page refreshes"""
        route.abort()

    # Setup route interception
    page.route(WEBPACK_SCRIPT_URL, handle_webpack_route)
    # Block HMR websocket and hot update requests
    page.route("**/ws", block_hmr_route)
    page.route("**/*.hot-update.*", block_hmr_route)

    # Remove webpack-dev-server overlay that can intercept clicks
    page.add_init_script(WEBPACK_OVERLAY_REMOVAL_SCRIPT)

    return page


@pytest.fixture
def window_open_stub(page: Page) -> Callable[[], list[str]]:
    """
    Fixture that stubs window.open() and tracks all opened URLs.

    Returns:
        A callable that returns the list of URLs opened via window.open()

    Example:
        def test_popup_opens_link(page, window_open_stub):
            page.goto(BASE_URL)
            page.click("text=Open Link")
            opened_urls = window_open_stub()
            assert len(opened_urls) == 1
            assert "google.com" in opened_urls[0]
    """
    opened_urls = []

    # Expose a function to capture window.open calls
    page.expose_function("__captureWindowOpen", lambda url: opened_urls.append(url))

    # Stub window.open in the page context
    page.add_init_script(
        """
        window.open = function(url, target, features) {
            window.__captureWindowOpen(url);
            return null;  // Prevent actual window opening
        };
    """
    )

    def get_opened_urls() -> list[str]:
        return opened_urls.copy()

    return get_opened_urls


@pytest.fixture
def mobile_page(browser, webpack_script: str, request) -> Generator[Page, None, None]:
    """
    Fixture that creates a page with proper mobile device emulation.

    This fixture creates a new browser context with the correct user agent,
    ensuring that react-device-detect properly identifies the device as mobile.

    The device configuration is passed via parametrize with the 'device_name' parameter.

    Example:
        @pytest.mark.parametrize("device_name", ALL_MOBILE_DEVICES)
        def test_mobile(mobile_page, device_name):
            mobile_page.goto(BASE_URL)
            # ... test mobile-specific behavior
    """
    # Get device_name from parametrize (safely handle missing callspec)
    callspec = getattr(request.node, "callspec", None)
    if callspec is None:
        raise ValueError(
            "mobile_page fixture requires @pytest.mark.parametrize with 'device_name' parameter"
        )
    device_name = callspec.params.get("device_name")
    if not device_name:
        raise ValueError(
            "mobile_page fixture requires 'device_name' parameter from @pytest.mark.parametrize"
        )

    try:
        device_config = MOBILE_DEVICES[device_name]
    except KeyError as e:
        raise ValueError(
            f"Unknown device_name={device_name}. Expected one of: {list(MOBILE_DEVICES)}"
        ) from e

    # Create a new context with mobile user agent
    context = browser.new_context(
        viewport=device_config["viewport"], user_agent=device_config["user_agent"]
    )

    # Create a page from this context
    page = context.new_page()

    # Setup webpack route interception (same as regular page fixture)
    def handle_webpack_route(route: Route) -> None:
        route.fulfill(
            status=200, content_type="application/javascript; charset=utf-8", body=webpack_script
        )

    def block_hmr_route(route: Route) -> None:
        """Block HMR/hot reload requests to prevent page refreshes"""
        route.abort()

    page.route(WEBPACK_SCRIPT_URL, handle_webpack_route)
    # Block HMR websocket and hot update requests
    page.route("**/ws", block_hmr_route)
    page.route("**/*.hot-update.*", block_hmr_route)

    # Remove webpack-dev-server overlay that can intercept clicks
    page.add_init_script(WEBPACK_OVERLAY_REMOVAL_SCRIPT)

    yield page

    # Cleanup
    page.close()
    context.close()


@pytest.fixture
def mobile_window_open_stub(mobile_page: Page) -> Callable[[], list[str]]:
    """
    Fixture that stubs window.open() for mobile pages and tracks all opened URLs.
    Same as window_open_stub but works with mobile_page fixture.
    """
    opened_urls = []

    # Expose a function to capture window.open calls
    mobile_page.expose_function("__captureWindowOpen", lambda url: opened_urls.append(url))

    # Stub window.open in the page context
    mobile_page.add_init_script(
        """
        window.open = function(url, target, features) {
            window.__captureWindowOpen(url);
            return null;  // Prevent actual window opening
        };
    """
    )

    def get_opened_urls() -> list[str]:
        return opened_urls.copy()

    return get_opened_urls


@pytest.fixture
def geolocation(context: BrowserContext) -> Callable[[float, float], None]:
    """
    Fixture that provides a function to set geolocation.

    Returns:
        A callable that sets the geolocation to the given lat/lon coordinates.

    Example:
        def test_my_location(page, geolocation):
            geolocation(50.0614, 19.9365)  # Krakow coordinates
            page.goto(BASE_URL)
            # ... test location-based functionality
    """
    # Grant geolocation permissions
    context.grant_permissions(["geolocation"])

    def set_location(latitude: float, longitude: float) -> None:
        """Set the browser geolocation"""
        context.set_geolocation({"latitude": latitude, "longitude": longitude})

    return set_location


@pytest.fixture
def performance_tracker() -> Callable:
    """
    Fixture for tracking performance metrics in stress tests.

    Returns:
        An object with methods to measure and retrieve run times.

    Example:
        def test_stress(page, performance_tracker):
            for i in range(5):
                start_time = time.time()
                # ... perform test actions
                elapsed_ms = (time.time() - start_time) * 1000
                performance_tracker.add_run(i + 1, elapsed_ms, marker_count)

            performance_tracker.save("test-results/stress-test-perf.json")
    """

    class PerformanceTracker:
        def __init__(self):
            self.run_times = []
            self.num_runs = 0
            self.expected_runs = 0

        def add_run(self, run_number: int, time_ms: float, markers: int):
            """Add a performance measurement"""
            self.run_times.append(
                {"run": run_number, "time": round(time_ms, 2), "markers": markers}
            )
            self.num_runs += 1

        def calculate_stats(self, max_allowed_ms: int = 25000):
            """Calculate performance statistics"""
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
            """Save performance data to JSON file"""
            stats = self.calculate_stats(max_allowed_ms)

            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, "w") as f:
                json.dump(stats, f, indent=2)

            print(f"\nPerformance data saved to {filepath}")
            if stats:
                print(f"Average time: {stats['avgTime']}ms")
                print(f"Max time: {stats['maxTime']}ms")
                print(f"Passed: {stats['passed']}")
            else:
                print("No runs recorded.")

    return PerformanceTracker()


# Export constants for use in tests
__all__ = [
    "ALL_MOBILE_DEVICES",
    "BASE_URL",
    "MAP_LOAD_TIMEOUT",
    "MARKER_LOAD_TIMEOUT",
    "MOBILE_DEVICES",
    "TABLE_LOAD_TIMEOUT",
    "TEST_LOCATIONS",
    "UI_VERTICAL_ALIGNMENT_TOLERANCE",
    "geolocation",
    "page",
    "performance_tracker",
    "webpack_script",
    "window_open_stub",
]

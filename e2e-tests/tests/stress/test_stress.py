"""
Stress Test

Tests application performance with large datasets (100,000 markers).
Measures page load time and marker rendering performance.
"""

import time

from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL, MARKER_LOAD_TIMEOUT


class TestStress:
    """Test suite for stress testing with large datasets"""

    def test_should_load_all_markers_and_measure_performance(self, page: Page, performance_tracker):
        """
        Load the map with 100k markers multiple times and measure performance.

        Performs 5 test runs, tracking:
        - Time to load and stabilize all markers
        - Number of visible markers/clusters
        - Performance statistics (avg, min, max times)

        Performance threshold: Max time < 25 seconds per run
        """
        num_runs = 5
        min_expected_markers = 10  # Minimum markers visible in initial viewport
        max_allowed_time_ms = 25000  # 25 seconds for 100k points with lazy loading

        performance_tracker.expected_runs = num_runs

        for run_number in range(1, num_runs + 1):
            print(f"\nRun {run_number} of {num_runs}")

            # Start timing
            start_time = time.time()

            # Navigate to the page
            page.goto(BASE_URL, wait_until="domcontentloaded")

            # Wait for first marker/cluster to appear (indicates map is loaded)
            # Use longer timeout for stress test since 100k markers take longer to load
            first_marker = page.locator(".leaflet-marker-icon, .leaflet-marker-cluster").first
            expect(first_marker).to_be_visible(timeout=max_allowed_time_ms)

            # Wait for markers to stabilize (stop increasing in count)
            # This ensures all initial markers are rendered
            previous_count = 0
            stable_count = 0  # Count consecutive stable readings
            max_attempts = 300  # 60 seconds at 200ms intervals
            attempt = 0

            while attempt < max_attempts:
                # Get current marker count
                current_count = page.locator(
                    ".leaflet-marker-icon, .leaflet-marker-cluster"
                ).count()

                # Check if count has stabilized
                if current_count == previous_count and current_count >= min_expected_markers:
                    stable_count += 1
                    # Require 2 consecutive stable readings
                    if stable_count >= 2:
                        break
                else:
                    stable_count = 0
                    if current_count != previous_count:
                        print(f"Marker count changed: {previous_count} -> {current_count}")

                previous_count = current_count
                time.sleep(0.2)
                attempt += 1

            if attempt >= max_attempts:
                raise TimeoutError(
                    f"Markers did not stabilize at minimum {min_expected_markers} within timeout"
                )

            # Get final marker count
            markers = page.locator(".leaflet-marker-icon, .leaflet-marker-cluster")
            marker_count = markers.count()

            # Calculate elapsed time
            end_time = time.time()
            elapsed_ms = (end_time - start_time) * 1000

            print(
                f"Run {run_number} took {elapsed_ms:.0f}ms "
                f"and loaded {marker_count} markers/clusters"
            )

            # Record performance data
            performance_tracker.add_run(run_number, elapsed_ms, marker_count)

            # Verify minimum number of markers are loaded
            assert (
                marker_count >= min_expected_markers
            ), f"Expected at least {min_expected_markers} markers but got {marker_count}"

            # Find visible elements not behind the left panel (x>220) or navbar (y>60)
            find_visible_js = """(selector) => {
                return Array.from(document.querySelectorAll(selector))
                    .find(el => {
                        const r = el.getBoundingClientRect();
                        return r.left > 220 && r.top > 60
                            && r.right < window.innerWidth
                            && r.bottom < window.innerHeight;
                    }) || null;
            }"""
            popup = page.locator(".leaflet-popup-content")

            # Click a cluster to zoom in
            cluster = page.evaluate_handle(find_visible_js, ".marker-cluster")
            assert cluster.as_element(), "No visible cluster found"
            cluster.as_element().click()

            # Wait for individual marker to appear after zoom
            individual_marker = page.locator(".leaflet-marker-icon:not(.marker-cluster)").first
            expect(individual_marker).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)

            # Click an individual marker to open its popup
            marker = page.evaluate_handle(
                find_visible_js,
                ".leaflet-marker-icon:not(.marker-cluster)",
            )
            assert marker.as_element(), "No visible individual marker found"
            marker.as_element().click()
            expect(popup).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)

            # Wait for content to load (popup initially shows "Loading...")
            title = popup.locator("h3")
            expect(title).to_be_visible(timeout=MARKER_LOAD_TIMEOUT)
            assert title.text_content(), "Popup title should not be empty"
            expect(popup.get_by_text("type_of_place").first).to_be_visible()
            expect(popup.get_by_text("accessible_by").first).to_be_visible()
            print(f"Popup verified for: {title.text_content()}")

        # Save performance data to JSON file
        performance_tracker.save("test-results/stress-test-perf.json", max_allowed_time_ms)

        # Calculate stats for assertions
        stats = performance_tracker.calculate_stats(max_allowed_time_ms)

        print("\nPerformance Summary:")
        print(f"  Avg: {stats['avgTime']}ms")
        print(f"  Max: {stats['maxTime']}ms")
        print(f"  Avg Markers: {stats['avgMarkers']}")

        # Assertions
        assert (
            stats["numRuns"] == num_runs
        ), f"Expected {num_runs} runs but only {stats['numRuns']} completed"

        assert (
            stats["maxTime"] < max_allowed_time_ms
        ), f"The slowest run ({stats['maxTime']}ms) should be below {max_allowed_time_ms}ms"

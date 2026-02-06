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
            max_attempts = 120  # 60 seconds at 500ms intervals
            attempt = 0

            while attempt < max_attempts:
                # Get current marker count
                current_count = page.locator(
                    ".leaflet-marker-icon, .leaflet-marker-cluster"
                ).count()

                # Check if count has stabilized
                if current_count == previous_count and current_count >= min_expected_markers:
                    stable_count += 1
                    # Require 3 consecutive stable readings
                    if stable_count >= 3:
                        break
                else:
                    stable_count = 0
                    if current_count != previous_count:
                        print(f"Marker count changed: {previous_count} -> {current_count}")

                previous_count = current_count
                time.sleep(0.5)
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

            # Click clusters until individual markers appear, then click a marker
            clusters = page.locator(".marker-cluster")
            individual_markers = page.locator(".leaflet-marker-icon:not(.marker-cluster)")
            popup = page.locator(".leaflet-popup-content")
            max_clicks = 20
            for i in range(max_clicks):
                if individual_markers.count() > 0:
                    break
                if clusters.count() == 0:
                    raise AssertionError("No clusters or individual markers found to click")
                clusters.first.click()
                print(f"Click {i + 1}: expanding cluster...")
                expect(page.locator(".leaflet-marker-icon").first).to_be_visible(
                    timeout=MARKER_LOAD_TIMEOUT
                )
            else:
                raise AssertionError(
                    f"No individual markers appeared after {max_clicks} cluster clicks"
                )

            # Click an individual marker to open its popup
            individual_markers.first.click()
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

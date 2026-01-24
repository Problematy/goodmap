"""
Test helper functions for Goodmap E2E tests.

Provides utility functions for:
- Test data constants
- Marker selection workarounds
- Popup content verification
- Problem form testing
"""

from typing import Any

from playwright.sync_api import ElementHandle, Page, expect

# Test data for Zwierzyniecka location
# Note: Category names are translated (e.g., "type_of_place" -> "type of place")
EXPECTED_PLACE_ZWIERZYNIECKA = {
    "title": "Zwierzyniecka",
    "subtitle": "small bridge",
    "categories": [
        ["type of place", "small bridge"],
        ["accessible by", "bikes, pedestrians"],
    ],
}


def get_rightmost_marker(page: Page) -> ElementHandle | None:
    """
    Workaround for selecting specific markers on the map.
    Finds the rightmost marker by comparing x-coordinates.

    Args:
        page: Playwright page object

    Returns:
        The rightmost marker element handle, or None if no markers found

    TODO: Find a better way to select specific markers by their properties.
    Consider adding data-testid attributes to markers in the backend/frontend.
    """
    # Use evaluate_handle to return a proper element handle instead of serialized null
    handle = page.evaluate_handle(
        """
        () => {
            const markers = document.querySelectorAll(
                '.leaflet-marker-icon, .leaflet-marker-cluster'
            );
            let rightmostMarker = null;
            let maxX = -Infinity;

            markers.forEach(marker => {
                const rect = marker.getBoundingClientRect();
                if (rect.x > maxX) {
                    maxX = rect.x;
                    rightmostMarker = marker;
                }
            });

            return rightmostMarker;
        }
    """
    )
    # Convert JSHandle to ElementHandle if it's an element, otherwise return None
    return handle.as_element()


def verify_popup_content(page: Page, expected_content: dict[str, Any]) -> None:
    """
    Verifies popup content including title, subtitle, categories, and CTA button.

    Scopes assertions to .leaflet-popup-content or .MuiDialogContent-root
    to avoid false positives from other elements on the page.

    Uses semantic element selectors (h3 for title, p for subtitle) for the new frontend.

    Args:
        page: Playwright page object
        expected_content: Expected content dictionary with keys:
            - title: Expected title text
            - subtitle: Expected subtitle text
            - categories: List of [category, value] tuples
            - CTA (optional): Dict with displayValue and value (URL)

    Example:
        verify_popup_content(page, {
            "title": "Bridge Name",
            "subtitle": "small bridge",
            "categories": [["type of place", "small bridge"]],
            "CTA": {"displayValue": "View on Map", "value": "https://..."}
        })
    """
    # Scope to popup container
    popup = page.locator(".leaflet-popup-content, .MuiDialogContent-root")

    # Verify title (h3 element in new frontend)
    title = popup.locator("h3")
    expect(title).to_have_text(expected_content["title"])

    # Verify subtitle (p element after title in new frontend)
    subtitle = popup.locator("p").first
    expect(subtitle).to_have_text(expected_content["subtitle"])

    # Verify categories
    # Note: We only check that category labels are visible
    # The values may appear in multiple places (subtitle + category value)
    # so we check for their presence at least once
    for category, value in expected_content["categories"]:
        expect(popup.get_by_text(category).first).to_be_visible()
        # Check that the value appears at least once in the popup
        expect(popup.get_by_text(value).first).to_be_visible()

    # Verify and click CTA button if provided
    if "CTA" in expected_content:
        cta = expected_content["CTA"]
        cta_button = popup.locator("button", has_text=cta["displayValue"])
        expect(cta_button).to_be_visible()
        cta_button.click()


def verify_problem_form(page: Page) -> None:
    """
    Verifies the problem reporting form functionality.
    Tests form visibility, option selection, custom input, and API submission.

    Args:
        page: Playwright page object
    """
    # Click "report a problem" link using JavaScript to bypass any overlay issues
    # force=True still clicks at coordinates which can be intercepted on CI
    report_link = page.locator("text=report a problem")
    expect(report_link).to_be_visible()
    report_link.scroll_into_view_if_needed()
    # Use dispatchEvent to trigger click directly on the element (cannot be intercepted)
    report_link.evaluate("el => el.click()")

    # Wait for form to appear inside the popup
    # Scope to popup to avoid matching the filter form
    popup = page.locator(".leaflet-popup-content, .MuiDialogContent-root")
    form = popup.locator("form")
    expect(form).to_be_visible()

    # Verify dropdown has expected options
    dropdown = form.locator("select")
    expect(dropdown).to_be_visible()

    options_text = dropdown.locator("option").all_text_contents()
    # Check that all problem type options exist
    expected_options = [
        "this point is not here",
        "it's overloaded",
        "it's broken",
        "other",
    ]

    for expected_option in expected_options:
        assert expected_option in options_text, f"Option '{expected_option}' not found in dropdown"

    assert any(
        "Please choose an option" in opt for opt in options_text
    ), "Placeholder option not found in dropdown"

    # Setup API response listener
    def is_report_location_post(response):
        return "/api/report-location" in response.url and response.request.method == "POST"

    with page.expect_response(is_report_location_post, timeout=10000) as response_info:
        # Select "other" option
        dropdown.select_option("other")

        # Fill in custom problem description
        problem_input = form.locator('input[type="text"]').first
        expect(problem_input).to_be_visible()
        problem_input.fill("Custom issue description")

        # Submit the form
        # Use JavaScript click to bypass webpack overlay that may intercept clicks on CI
        submit_button = form.locator('input[type="submit"]').first
        expect(submit_button).to_be_visible()
        submit_button.evaluate("el => el.click()")

    # Verify API response
    response = response_info.value
    assert response.status == 200, f"Expected status 200, got {response.status}"

    response_body = response.json()
    assert (
        response_body.get("message") == "Location reported"
    ), f"Expected message 'Location reported', got {response_body.get('message')}"

    # Verify success message appears and form disappears
    success_message = popup.get_by_text("Location reported")
    expect(success_message).to_be_visible()
    expect(form).not_to_be_visible()

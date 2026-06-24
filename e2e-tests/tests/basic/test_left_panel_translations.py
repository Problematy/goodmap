"""
Test suite for left panel field translations.

Tests that category names, filter options, and help texts in the left panel
are properly translated when switching languages.
"""

import pytest
from playwright.sync_api import Page, expect

from tests.conftest import BASE_URL

# Expected translations for left panel fields
TRANSLATIONS = {
    "en": {
        "category_names": {
            "accessible_by": "accessible by",
            "type_of_place": "type of place",
        },
        "filter_options": {
            "bikes": "bikes",
            "cars": "cars",
            "pedestrians": "pedestrians",
            "big bridge": "big bridge",
            "small bridge": "small bridge",
        },
        "help_texts": {
            "categories_help_accessible_by": "Who can use this bridge",
            "categories_options_help_small bridge": "A smaller pedestrian or bike bridge",
        },
    },
    "pl": {
        "category_names": {
            "accessible_by": "dostępny dla",
            "type_of_place": "typ miejsca",
        },
        "filter_options": {
            "bikes": "rowery",
            "cars": "samochody",
            "pedestrians": "piesi",
            "big bridge": "duży most",
            "small bridge": "mały most",
        },
        "help_texts": {
            "categories_help_accessible_by": "Kto może korzystać z tego mostu",
            "categories_options_help_small bridge": "Mniejszy most dla pieszych lub rowerzystów",
        },
    },
}


def get_language_button(page: Page):
    """Get language switch button using ID selector."""
    return page.locator("#languages-menu")


def switch_to_language(page: Page, lang_name: str):
    """Switch to a specific language by clicking the language menu."""
    get_language_button(page).click()
    page.get_by_role("link", name=lang_name).click()
    page.wait_for_load_state("domcontentloaded")


class TestLeftPanelTranslationsEnglish:
    """Test suite for left panel translations in English (default language)"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to home page and wait for filter form to load"""
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        # Auto-wait for content to be fully loaded
        panel = page.locator("#left-panel")
        expect(panel).to_contain_text("accessible by", ignore_case=True, timeout=10000)

    def test_category_names_in_english(self, page: Page):
        """Verify category names are displayed in English"""
        panel = page.locator("#left-panel")
        for key, expected in TRANSLATIONS["en"]["category_names"].items():
            expect(panel).to_contain_text(
                expected, ignore_case=True
            ), f"Expected '{expected}' (translation of '{key}') in left panel"

    def test_filter_options_in_english(self, page: Page):
        """Verify filter options are displayed in English"""
        panel = page.locator("#left-panel")
        for key, expected in TRANSLATIONS["en"]["filter_options"].items():
            expect(panel).to_contain_text(
                expected, ignore_case=True
            ), f"Expected '{expected}' (translation of '{key}') in left panel"


class TestLeftPanelTranslationsPolish:
    """Test suite for left panel translations in Polish"""

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to home page, switch to Polish, and wait for filter form"""
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        switch_to_language(page, "polski")
        # Use expect().to_contain_text() to auto-wait for translated content
        panel = page.locator("#left-panel")
        expect(panel).to_contain_text("dostępny dla", ignore_case=True, timeout=10000)

    def test_category_names_in_polish(self, page: Page):
        """Verify category names are displayed in Polish"""
        panel = page.locator("#left-panel")
        for key, expected in TRANSLATIONS["pl"]["category_names"].items():
            expect(panel).to_contain_text(
                expected, ignore_case=True
            ), f"Expected '{expected}' (Polish translation of '{key}') in left panel"

    def test_filter_options_in_polish(self, page: Page):
        """Verify filter options are displayed in Polish"""
        panel = page.locator("#left-panel")
        for key, expected in TRANSLATIONS["pl"]["filter_options"].items():
            expect(panel).to_contain_text(
                expected, ignore_case=True
            ), f"Expected '{expected}' (Polish translation of '{key}') in left panel"


class TestLeftPanelTranslationSwitching:
    """Test suite for switching languages and verifying translations update"""

    def test_switch_from_english_to_polish_updates_category_names(self, page: Page):
        """Verify switching from English to Polish updates category names"""
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        panel = page.locator("#left-panel")

        # Verify English first (auto-wait for content)
        expect(panel).to_contain_text("accessible by", ignore_case=True, timeout=10000)

        # Switch to Polish and verify (auto-wait for translated content)
        switch_to_language(page, "polski")
        expect(panel).to_contain_text("dostępny dla", ignore_case=True, timeout=10000)

    def test_switch_from_polish_to_english_updates_category_names(self, page: Page):
        """Verify switching from Polish back to English restores English text"""
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        panel = page.locator("#left-panel")

        # Switch to Polish first and verify (auto-wait for translated content)
        switch_to_language(page, "polski")
        expect(panel).to_contain_text("dostępny dla", ignore_case=True, timeout=10000)

        # Switch back to English and verify (auto-wait for translated content)
        switch_to_language(page, "English")
        expect(panel).to_contain_text("accessible by", ignore_case=True, timeout=10000)


class TestLeftPanelHelpTextTranslations:
    """Test suite for filter help text translations"""

    def test_help_tooltip_in_english(self, page: Page):
        """Verify help tooltip shows English text"""
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        # Auto-wait for content to be fully loaded
        panel = page.locator("#left-panel")
        expect(panel).to_contain_text("accessible by", ignore_case=True, timeout=10000)

        # Find and hover over a help icon (label is "Help: {translated_text}")
        expected = TRANSLATIONS["en"]["help_texts"]["categories_options_help_small bridge"]
        help_icon = page.get_by_label(f"Help: {expected}")
        assert help_icon.count() > 0, "Help icon not found - UI may have changed"
        help_icon.first.hover()
        tooltip = page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        tooltip_text = tooltip.inner_text()
        assert expected in tooltip_text, f"Expected '{expected}' in tooltip"

    def test_help_tooltip_in_polish(self, page: Page):
        """Verify help tooltip shows Polish text after language switch"""
        page.set_viewport_size({"width": 1200, "height": 800})
        page.goto(BASE_URL, wait_until="domcontentloaded")
        switch_to_language(page, "polski")
        # Auto-wait for translated content before interacting with help icon
        panel = page.locator("#left-panel")
        expect(panel).to_contain_text("dostępny dla", ignore_case=True, timeout=10000)

        # Find and hover over a help icon (label is "Help: {translated_text}")
        expected = TRANSLATIONS["pl"]["help_texts"]["categories_options_help_small bridge"]
        help_icon = page.get_by_label(f"Help: {expected}")
        assert help_icon.count() > 0, "Help icon not found - UI may have changed"
        help_icon.first.hover()
        tooltip = page.locator('[role="tooltip"]')
        expect(tooltip).to_be_visible()
        tooltip_text = tooltip.inner_text()
        assert expected in tooltip_text, f"Expected '{expected}' in tooltip"

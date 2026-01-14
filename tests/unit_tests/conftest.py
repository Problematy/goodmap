import json
from typing import Any

import deprecation
import pytest

from goodmap.config import GoodmapConfig
from goodmap.goodmap import create_app_from_config


def fake_translation(key: str):
    return f"{key}-translated"


def get_test_config_data() -> dict[str, Any]:
    """Return the common configuration data used by test fixtures."""
    return {
        "APP_NAME": "testing App Name",
        "SECRET_KEY": "secret",
        "USE_WWW": False,
        "TRANSLATION_DIRECTORIES": ["/some/fake/dir"],
        "LANGUAGES": {
            "en": {"name": "English", "flag": "uk", "country": "GB"},
        },
        "DB": {
            "TYPE": "json",
            "DATA": {
                "site_content": {"pages": []},
                "categories": {"test-category": ["test", "test2"]},
                "locations": [],
                "data": [
                    {
                        "name": "test",
                        "position": [50, 50],
                        "test_category": ["test"],
                        "type_of_place": "test-place",
                        "uuid": "1",
                        "remark": "this is a remark",
                    },
                    {
                        "name": "test2",
                        "position": [60, 60],
                        "test_category": ["second-category"],
                        "type_of_place": "test-place2",
                        "uuid": "2",
                    },
                ],
                "meta_data": ["uuid"],
                "visible_data": ["name", "test_category", "type_of_place"],
                "categories_help": ["test-category"],
                "categories_options_help": {
                    "test-category": ["test"],
                },
                "location_obligatory_fields": [
                    ("test_category", "list[str]"),
                    ("type_of_place", "str"),
                    ("name", "str"),
                ],
                "suggestions": [],
                "reports": [],
            },
        },
    }


# --- Helper functions for cleaner tests ---


def api_post(client, url, data):
    """Helper for JSON POST requests."""
    return client.post(url, data=json.dumps(data), content_type="application/json")


def api_put(client, url, data):
    """Helper for JSON PUT requests."""
    return client.put(url, data=json.dumps(data), content_type="application/json")


def api_delete(client, url):
    """Helper for DELETE requests."""
    return client.delete(url)


def create_test_app(feature_flags=None, db_overrides=None):
    """Create a test app with optional feature flags and db overrides."""
    config_data = get_test_config_data()
    if feature_flags is None:
        feature_flags = {"CATEGORIES_HELP": True, "USE_LAZY_LOADING": True, "ENABLE_ADMIN_PANEL": True}
    config_data["FEATURE_FLAGS"] = feature_flags
    if db_overrides:
        config_data["DB"]["DATA"].update(db_overrides)
    config = GoodmapConfig.model_validate(config_data)
    app = create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    return app.test_client()


# --- Fixtures ---


@pytest.fixture
def test_app():
    return create_test_app()


@deprecation.deprecated(
    deprecated_in="0.5.3",
    removed_in="0.6.0",
    details="actually categories_help should be integrated as true in future major release",
)
@pytest.fixture
def test_app_without_helpers():
    return create_test_app(feature_flags={"CATEGORIES_HELP": False})

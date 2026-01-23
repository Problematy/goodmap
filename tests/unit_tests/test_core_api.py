import json
from unittest import mock

import pytest

from goodmap.config import GoodmapConfig
from goodmap.core_api import get_or_none, make_tuple_translation
from goodmap.goodmap import create_app_from_config
from tests.unit_tests.conftest import (
    api_post,
    create_test_app,
    fake_translation,
    get_test_config_data,
)

# --- Basic endpoint tests ---


def test_language_endpoint_returns_languages(test_app):
    response = test_app.get("/api/languages")
    assert response.status_code == 200
    assert response.json == {"en": {"country": "GB", "flag": "uk", "name": "English"}}


@mock.patch("importlib.metadata.version", return_value="0.1.2")
def test_version_endpoint_returns_version(mock_returning_version, test_app):
    response = test_app.get("/api/version")
    mock_returning_version.assert_called_once_with("goodmap")
    assert response.status_code == 200
    assert response.json == {"backend": "0.1.2"}


def test_csrf_token_endpoint_returns_token(test_app):
    response = test_app.get("/api/generate-csrf-token")
    assert response.status_code == 200
    assert "csrf_token" in response.json


def test_api_doc_index(test_app):
    response = test_app.get("/api/doc")
    assert response.status_code == 200
    assert response.content_type == "text/html"
    assert b"/api/doc/swagger/" in response.data
    assert b"/api/doc/redoc/" in response.data
    assert b"/api/doc/openapi.json" in response.data


# --- Categories endpoint tests ---


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_endpoints_return_expected_data(test_app):
    # Test /api/categories endpoint
    response = test_app.get("/api/categories")
    assert response.status_code == 200
    assert response.json == {
        "categories": [["test-category", "test-category-translated"]],
        "categories_help": [{"test-category": "categories_help_test-category-translated"}],
    }

    # Test /api/category/<category> endpoint
    response = test_app.get("/api/category/test-category")
    assert response.status_code == 200
    assert response.json == {
        "categories_options": [["test", "test-translated"], ["test2", "test2-translated"]],
        "categories_options_help": [{"test": "categories_options_help_test-translated"}],
    }


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_endpoints_old_format(test_app_without_helpers):
    # Test /api/categories endpoint (old format)
    response = test_app_without_helpers.get("/api/categories")
    assert response.status_code == 200
    assert response.json == [["test-category", "test-category-translated"]]

    # Test /api/category/<category> endpoint (old format)
    response = test_app_without_helpers.get("/api/category/test-category")
    assert response.status_code == 200
    assert response.json == [["test", "test-translated"], ["test2", "test2-translated"]]


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_categories_endpoint_with_categories_help():
    test_app = create_test_app(
        feature_flags={"CATEGORIES_HELP": True},
        db_overrides={"categories_help": ["option1", "option2"]},
    )
    response = test_app.get("/api/categories")
    assert response.status_code == 200
    data = response.json
    assert data is not None
    assert "categories_help" in data
    assert len(data["categories_help"]) == 2
    assert data["categories_help"][0] == {"option1": "categories_help_option1-translated"}


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_category_data_endpoint_with_categories_options_help():
    test_app = create_test_app(
        feature_flags={"CATEGORIES_HELP": True},
        db_overrides={"categories_options_help": {"test-category": ["help1", "help2"]}},
    )
    response = test_app.get("/api/category/test-category")
    assert response.status_code == 200
    data = response.json
    assert data is not None
    assert "categories_options_help" in data
    assert len(data["categories_options_help"]) == 2
    assert data["categories_options_help"][0] == {
        "help1": "categories_options_help_help1-translated"
    }


def test_categories_endpoint_with_none_categories_help():
    test_app = create_test_app(
        feature_flags={"CATEGORIES_HELP": True}, db_overrides={"categories_help": None}
    )
    response = test_app.get("/api/categories")
    assert response.status_code == 200
    data = response.json
    assert data is not None
    assert data["categories_help"] == []


def test_category_data_endpoint_with_none_categories_options_help():
    config_data = get_test_config_data()
    config_data["FEATURE_FLAGS"] = {"CATEGORIES_HELP": True}
    config_data["DB"]["DATA"].pop("categories_options_help", None)
    config = GoodmapConfig.model_validate(config_data)
    app = create_app_from_config(config)
    test_client = app.test_client()
    response = test_client.get("/api/category/test-category")
    assert response.status_code == 200
    data = response.json
    assert data is not None
    assert data["categories_options_help"] == []


# --- Categories-full endpoint tests ---


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_full_endpoint(test_app):
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json

    # Check structure
    assert "categories" in data
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) > 0

    # Check required fields and translations
    category = data["categories"][0]
    assert "key" in category
    assert "name" in category
    assert "options" in category
    assert category["key"] == "test-category"
    assert category["name"] == "test-category-translated"

    # Check options are translated tuples
    assert isinstance(category["options"], list)
    assert len(category["options"]) == 2
    assert category["options"][0] == ["test", "test-translated"]
    assert category["options"][1] == ["test2", "test2-translated"]


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_full_endpoint_with_multiple_categories():
    test_app = create_test_app(
        db_overrides={
            "categories": {
                "category1": ["opt1", "opt2"],
                "category2": ["opt3"],
            }
        }
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json
    assert data is not None
    assert len(data["categories"]) == 2
    keys = [cat["key"] for cat in data["categories"]]
    assert "category1" in keys
    assert "category2" in keys


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_full_endpoint_with_categories_help():
    test_app = create_test_app(
        feature_flags={"CATEGORIES_HELP": True},
        db_overrides={
            "categories": {"test-category": ["opt1", "opt2"]},
            "categories_help": ["test-category"],
            "categories_options_help": {"test-category": ["opt1"]},
        },
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json
    assert data is not None

    # Check categories_help at response level
    assert "categories_help" in data
    assert len(data["categories_help"]) == 1
    assert data["categories_help"][0] == {
        "test-category": "categories_help_test-category-translated"
    }

    # Check options_help at category level
    category = data["categories"][0]
    assert "options_help" in category
    assert len(category["options_help"]) == 1
    assert category["options_help"][0] == {"opt1": "categories_options_help_opt1-translated"}


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_full_endpoint_without_categories_help():
    test_app = create_test_app(
        feature_flags={"CATEGORIES_HELP": False},
        db_overrides={
            "categories": {"test-category": ["opt1", "opt2"]},
        },
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json
    assert data is not None

    # When CATEGORIES_HELP is False, no help data should be included
    assert "categories_help" not in data
    category = data["categories"][0]
    assert "options_help" not in category


# --- Locations endpoint tests ---


def test_get_locations(test_app):
    response = test_app.get("/api/locations")
    assert response.status_code == 200
    assert response.json == [
        {"uuid": "1", "position": [50, 50], "remark": True},
        {"uuid": "2", "position": [60, 60], "remark": False},
    ]


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("goodmap.formatter.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_get_location(test_app):
    response = test_app.get("/api/location/1")
    assert response.status_code == 200
    assert response.json == {
        "data": [
            ["name-translated", "test-translated"],
            ["test_category-translated", ["test-translated"]],
            ["type_of_place-translated", "test-place-translated"],
        ],
        "metadata": {"uuid-translated": "1-translated"},
        "position": [50.0, 50.0],
        "subtitle": "test-place-translated",
        "title": "test",
    }


def test_get_location_not_found(test_app):
    response = test_app.get("/api/location/non-existent-uuid")
    assert response.status_code == 404
    assert response.json["message"] == "Location not found"


# --- Report location tests ---


def test_reporting_location_success(test_app):
    response = api_post(
        test_app, "/api/report-location", {"id": "location-id", "description": "some error"}
    )
    assert response.status_code == 200


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_reporting_returns_error_when_wrong_json(test_app):
    response = api_post(test_app, "/api/report-location", {"name": "location-id", "position": 50})
    assert response.status_code == 422
    assert isinstance(response.json, list)


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_report_location_notification_success(test_app):
    response = api_post(
        test_app, "/api/report-location", {"id": "test-location", "description": "Test description"}
    )
    assert response.status_code == 200
    assert response.json["message"] == "Location reported-translated"


def test_report_location_with_invalid_json(test_app):
    response = test_app.post(
        "/api/report-location", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 422


def test_report_location_unexpected_error(test_app):
    db = test_app.application.db
    with mock.patch.object(db, "add_report", side_effect=Exception("Database failure")):
        response = api_post(
            test_app, "/api/report-location", {"id": "test-id", "description": "Test report"}
        )
        assert response.status_code == 500


# --- Suggest location tests ---


def test_suggest_new_location_with_valid_data(test_app):
    response = api_post(
        test_app,
        "/api/suggest-new-point",
        {
            "uuid": "one",
            "name": "Test Organization",
            "type_of_place": "type",
            "test_category": ["test"],
            "position": [50, 50],
        },
    )
    assert response.status_code == 200
    assert response.json == {"message": "Location suggested"}


def test_suggest_new_location_with_multipart_form_data(test_app):
    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Organization",
            "type_of_place": "type",
            "test_category": json.dumps(["test"]),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200


# --- Photo upload tests ---

# Minimal valid JPEG (1x1 pixel red image)
MINIMAL_JPEG = bytes(
    [
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xBA, 0xAE, 0xEB,
        0x91, 0x19, 0xFF, 0xD9,
    ]
)

# Minimal PNG (1x1 pixel)
MINIMAL_PNG = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
        0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, 0xDE, 0x00, 0x00, 0x00,
        0x0C, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59, 0xE7, 0x00, 0x00, 0x00,
        0x00, 0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ]
)


def test_suggest_location_with_valid_jpeg_photo(test_app):
    """Valid JPEG photo upload should succeed."""
    from io import BytesIO

    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": json.dumps(["test"]),
            "photo": (BytesIO(MINIMAL_JPEG), "photo.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert response.json == {"message": "Location suggested"}


def test_suggest_location_rejects_png_photo(test_app):
    """PNG photos should be rejected (only JPEG allowed)."""
    from io import BytesIO

    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": json.dumps(["test"]),
            "photo": (BytesIO(MINIMAL_PNG), "photo.png"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]
    assert "jpeg" in response.json["message"].lower()


def test_suggest_location_rejects_wrong_extension(test_app):
    """JPEG content with wrong extension should be rejected."""
    from io import BytesIO

    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": json.dumps(["test"]),
            "photo": (BytesIO(MINIMAL_JPEG), "photo.gif"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]


def test_suggest_location_rejects_oversized_photo(test_app):
    """Photos over 5MB should be rejected."""
    from io import BytesIO

    # Create a file just over 5MB
    oversized_content = MINIMAL_JPEG + (b"\x00" * (5 * 1024 * 1024 + 1))

    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": json.dumps(["test"]),
            "photo": (BytesIO(oversized_content), "photo.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]
    assert "5MB" in response.json["message"]


def test_suggest_location_rejects_fake_jpeg(test_app):
    """Text file claiming to be JPEG should be rejected by content validation."""
    from io import BytesIO

    fake_jpeg = b"This is not a JPEG file, just plain text"

    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": json.dumps(["test"]),
            "photo": (BytesIO(fake_jpeg), "photo.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]


def test_suggest_location_with_photo_stores_suggestion(test_app):
    """Verify that location with photo is stored in database."""
    from io import BytesIO

    db = test_app.application.db
    initial_count = len(db.get_suggestions({}))

    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "position": json.dumps([50, 50]),
            "name": "Test Location With Photo",
            "type_of_place": "test-place",
            "test_category": json.dumps(["test"]),
            "photo": (BytesIO(MINIMAL_JPEG), "photo.jpg"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 200

    # Verify suggestion was stored
    suggestions = db.get_suggestions({})
    assert len(suggestions) == initial_count + 1
    assert suggestions[-1]["name"] == "Test Location With Photo"


@pytest.mark.parametrize(
    "data,expected_status",
    [
        ({"photo": "Test Photo"}, 400),  # missing required fields
        ({}, 400),  # empty data
        ({"name": 123, "position": 456, "photo": "Test Photo"}, 400),  # invalid types
        ({"invalid": "data"}, 400),  # wrong fields
    ],
)
def test_suggest_new_location_invalid_data(test_app, data, expected_status):
    response = api_post(test_app, "/api/suggest-new-point", data)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "body,expected_message",
    [
        ("", "Invalid request data"),
        ("{invalid json", "Invalid request data"),
        ("null", "Invalid request data"),
    ],
)
def test_suggest_new_location_malformed_body(test_app, body, expected_message):
    response = test_app.post("/api/suggest-new-point", data=body, content_type="application/json")
    assert response.status_code == 400
    assert response.json["message"] == expected_message


def test_suggest_new_location_with_list_item_too_long(test_app):
    long_item = "x" * 101
    response = api_post(
        test_app,
        "/api/suggest-new-point",
        {
            "name": "Test Location",
            "position": [50.5, 19.5],
            "type_of_place": "test-place",
            "test_category": [long_item],
        },
    )
    assert response.status_code == 400
    assert response.json["message"] == "Invalid location data"


def test_suggest_location_unexpected_error(test_app):
    db = test_app.application.db
    with mock.patch.object(db, "add_suggestion", side_effect=Exception("Database failure")):
        response = api_post(
            test_app,
            "/api/suggest-new-point",
            {
                "name": "Test",
                "position": [50, 50],
                "test_category": ["test"],
                "type_of_place": "test",
            },
        )
        assert response.status_code == 500
        assert "An error occurred while processing your suggestion" in response.json["message"]


# --- DoS protection tests ---


@pytest.mark.parametrize(
    "field_name,malicious_value,error_substring",
    [
        ("position", '{"a":{"b":{"c":"d"}}}', "too complex"),  # deeply nested object
        ("position", '[[["deeply", "nested"]]]', "too complex"),  # deeply nested array
        ("position", '["' + "x" * (55 * 1024) + '"]', "too large"),  # oversized payload
    ],
)
def test_suggest_location_dos_protection(test_app, field_name, malicious_value, error_substring):
    response = test_app.post(
        "/api/suggest-new-point",
        data={
            "name": "Test",
            field_name: malicious_value,
            "test_category": json.dumps(["test"]),
            "type_of_place": "test-place",
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.json
    assert (
        error_substring in data["message"].lower()
        or error_substring in data.get("error", "").lower()
    )


def test_suggest_location_dos_protection_json_body_deeply_nested(test_app):
    response = test_app.post(
        "/api/suggest-new-point",
        data='{"a":{"b":{"c":"d"}}}',
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.json
    assert (
        "too complex" in data["message"].lower() or "nesting depth" in data.get("error", "").lower()
    )


# --- Location clustering tests ---


def test_location_clustering_basic(test_app):
    response = test_app.get("/api/locations-clustered")
    assert response.status_code == 200


def test_location_clustering_high_zoom_no_clusters(test_app):
    response = test_app.get("/api/locations-clustered?zoom=16")
    assert response.status_code == 200
    data = response.json
    assert data[0]["type"] == "point"
    assert data[1]["type"] == "point"


def test_location_clustering_low_zoom_creates_clusters(test_app):
    response = test_app.get("/api/locations-clustered?zoom=1")
    assert response.status_code == 200
    data = response.json
    assert len(data) == 1
    assert data[0]["type"] == "cluster"


@pytest.mark.parametrize(
    "zoom,expected_status,check_message",
    [
        ("invalid", 400, "Invalid parameters provided"),
        ("-1", 400, "Zoom must be between 0 and 16"),
        ("17", 400, "Zoom must be between 0 and 16"),
        ("0", 200, None),
        ("16", 200, None),
    ],
)
def test_location_clustering_zoom_validation(test_app, zoom, expected_status, check_message):
    response = test_app.get(f"/api/locations-clustered?zoom={zoom}")
    assert response.status_code == expected_status
    if check_message:
        assert check_message in response.json["message"]


def test_location_clustering_empty_locations():
    test_app = create_test_app(db_overrides={"data": []})
    response = test_app.get("/api/locations-clustered?zoom=10")
    assert response.status_code == 200
    assert response.json == []


def test_location_clustering_exception_handling(test_app):
    with mock.patch(
        "goodmap.core_api.pysupercluster.SuperCluster", side_effect=Exception("Clustering failed")
    ):
        response = test_app.get("/api/locations-clustered?zoom=10")
        assert response.status_code == 500
        assert "An error occurred during clustering" in response.json["message"]


def test_location_clustering_logs_on_invalid_parameter(test_app):
    with mock.patch("goodmap.core_api.logger") as mock_logger:
        test_app.get("/api/locations-clustered?zoom=invalid")
        mock_logger.warning.assert_called_once()
        assert "Invalid parameter" in mock_logger.warning.call_args[0][0]


def test_location_clustering_logs_on_exception(test_app):
    with (
        mock.patch(
            "goodmap.core_api.pysupercluster.SuperCluster",
            side_effect=Exception("Clustering failed"),
        ),
        mock.patch("goodmap.core_api.logger") as mock_logger,
    ):
        test_app.get("/api/locations-clustered?zoom=10")
        mock_logger.error.assert_called_once()
        assert "Clustering operation failed" in mock_logger.error.call_args[0][0]
        assert mock_logger.error.call_args[1]["exc_info"] is True


# --- Helper function tests ---


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_make_tuple_translation():
    keys = ["alpha", "beta"]
    assert make_tuple_translation(keys) == [
        ("alpha", "alpha-translated"),
        ("beta", "beta-translated"),
    ]


@pytest.mark.parametrize(
    "data,keys,expected",
    [
        ({"a": {"b": {"c": "value"}}}, ("a", "b", "c"), "value"),
        ({"a": "not_a_dict"}, ("a", "b"), None),
        ({"a": {"b": "value"}}, ("a", "missing_key"), None),
    ],
)
def test_get_or_none(data, keys, expected):
    result = get_or_none(data, *keys)
    assert result == expected


def test_get_locations_from_request_helper(test_app):
    from goodmap.core_api import get_locations_from_request

    class MockArgs:
        def to_dict(self, flat=False):
            return {}

    mock_request_args = MockArgs()

    with test_app.application.app_context():
        locations = get_locations_from_request(test_app.application.db, mock_request_args)
        assert isinstance(locations, list)
        if locations:
            assert isinstance(locations[0], dict)
            assert "uuid" in locations[0]
            assert "position" in locations[0]

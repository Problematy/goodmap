from io import BytesIO
from unittest import mock

import pytest

from goodmap.api.core_api import get_default_issue_options, make_tuple_translation
from goodmap.config import GoodmapConfig
from goodmap.feature_flags import CategoriesHelp
from goodmap.goodmap import create_app_from_config
from tests.unit_tests.conftest import (
    api_post,
    create_test_app,
    fake_translation,
    get_test_config_data,
    make_flag_set,
    multipart_suggest_post,
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


def test_location_schema_endpoint_describes_this_instance(test_app):
    response = test_app.get("/api/location-schema")
    assert response.status_code == 200
    body = response.json
    assert set(body) == {
        "fields",
        "obligatory_fields",
        "reported_issue_types",
        "photo",
    }
    # uuid is server-assigned and must not be offered as a form field; position is
    # required and client-supplied, same as /api/suggest-new-point, so it must be.
    assert "uuid" not in body["fields"]
    assert "position" in body["fields"]
    assert all(set(t) == {"value", "label"} for t in body["reported_issue_types"])
    assert set(body["photo"]) == {"allowed_extensions", "allowed_mime_types", "max_size_bytes"}


def test_location_schema_reports_allowed_values_inside_each_field():
    """A field's allowed values are part of its own schema under `fields`.

    Removing the top-level `categories` key removed a second copy of them in a different
    shape, not the values themselves - a client building a suggest payload still needs
    them, and this is where it reads them from.
    """
    test_app = create_test_app(
        db_overrides={
            "categories": {"accessible_by": ["bikes", "cars"]},
            "location_obligatory_fields": [("accessible_by", "list"), ("name", "str")],
        }
    )
    response = test_app.get("/api/location-schema")
    assert response.status_code == 200
    body = response.json
    assert body is not None
    # frozenset-backed, so the order carries no meaning
    assert set(body["fields"]["accessible_by"]["enum_items"]) == {"bikes", "cars"}


def test_location_schema_endpoint_falls_back_to_default_issue_options():
    """An unconfigured reported_issue_types must not undersell what
    /api/report-location actually accepts (it falls back to the same defaults).
    """
    test_app = create_test_app(db_overrides={"reported_issue_types": []})
    response = test_app.get("/api/location-schema")
    assert response.status_code == 200
    data = response.json
    assert data is not None
    values = {t["value"] for t in data["reported_issue_types"]}
    assert values == set(get_default_issue_options())


def test_api_doc_index(test_app):
    response = test_app.get("/api/doc")
    assert response.status_code == 200
    assert response.content_type == "text/html"
    assert b"/api/doc/swagger/" in response.data
    assert b"/api/doc/redoc/" in response.data
    assert b"/api/doc/openapi.json" in response.data


# --- Categories-full endpoint tests ---


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
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

    # No default-checked options configured for this category
    assert category["default_checked"] == []

    # Categories without an explicit filter mode default to "or"
    assert category["filter_mode"] == "or"


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_categories_full_endpoint_reports_configured_filter_mode():
    test_app = create_test_app(
        db_overrides={
            "categories": {"test-category": ["opt1", "opt2"]},
            "categories_filter_mode": {"test-category": "exclusive"},
        }
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    assert response.json is not None
    category = response.json["categories"][0]
    assert category["filter_mode"] == "exclusive"


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_categories_full_endpoint_with_default_checked():
    test_app = create_test_app(
        db_overrides={
            "categories": {"test-category": ["opt1", "opt2"]},
            "categories_default_checked": {"test-category": ["opt1"]},
        }
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json
    assert data is not None

    category = data["categories"][0]
    assert category["default_checked"] == ["opt1"]


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_categories_full_endpoint_drops_default_checked_not_in_options():
    test_app = create_test_app(
        db_overrides={
            "categories": {"test-category": ["opt1", "opt2"]},
            "categories_default_checked": {"test-category": ["opt1", "not-an-option"]},
        }
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json
    assert data is not None

    category = data["categories"][0]
    assert category["default_checked"] == ["opt1"]


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_categories_full_endpoint_without_default_checked():
    test_app = create_test_app(
        db_overrides={
            "categories": {"test-category": ["opt1", "opt2"]},
        }
    )
    response = test_app.get("/api/categories-full")
    assert response.status_code == 200
    data = response.json
    assert data is not None

    category = data["categories"][0]
    assert category["default_checked"] == []


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
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


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_categories_full_endpoint_with_categories_help():
    test_app = create_test_app(
        feature_flags=make_flag_set(CategoriesHelp),
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


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_categories_full_endpoint_without_categories_help():
    test_app = create_test_app(
        feature_flags=make_flag_set(),
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
        {
            "uuid": "11111111-1111-1111-1111-111111111111",
            "position": [50, 50],
            "has_remark": True,
        },
        {
            "uuid": "22222222-2222-2222-2222-222222222222",
            "position": [60, 60],
            "has_remark": False,
        },
    ]


@pytest.mark.parametrize(
    "query",
    [
        "lat=abc",  # not a number
        "lat=999",  # outside -90..90
        "lon=999",  # outside -180..180
        "limit=notanumber",
        "limit=0",  # a limit of nothing is a caller mistake, not an empty map
        "limit=-3",
    ],
)
def test_get_locations_rejects_unusable_parameters(test_app, query):
    """lat/lon/limit values that cannot mean anything are reported, not ignored."""
    response = test_app.get(f"/api/locations?{query}")
    assert response.status_code == 400
    assert response.json["message"] == "Invalid request data"


@pytest.mark.parametrize(
    "query",
    [
        "",
        "lat=51.1&lon=17.05&limit=5",
        "unknown_param=x",  # not declared, and cannot be - filters are per-deployment
        "test-category=test",
    ],
)
def test_get_locations_accepts_valid_and_undeclared_parameters(test_app, query):
    """Declared params are checked; anything else passes through to the filters."""
    response = test_app.get(f"/api/locations?{query}")
    assert response.status_code == 200


def test_get_locations_multi_value_same_category_uses_or_semantics():
    """Selecting several checkboxes within one category should return the union
    of matches, not only entries that have every selected value."""
    client = create_test_app(
        db_overrides={
            "categories": {"tags": ["red", "blue", "green"]},
            "location_obligatory_fields": [("tags", "list"), ("name", "str")],
            "data": [
                {
                    "name": "red-only",
                    "position": [50, 50],
                    "tags": ["red"],
                    "uuid": "11111111-1111-1111-1111-111111111111",
                },
                {
                    "name": "blue-only",
                    "position": [60, 60],
                    "tags": ["blue"],
                    "uuid": "22222222-2222-2222-2222-222222222222",
                },
                {
                    "name": "green-only",
                    "position": [70, 70],
                    "tags": ["green"],
                    "uuid": "33333333-3333-3333-3333-333333333333",
                },
            ],
            "visible_data": ["name", "tags"],
        }
    )

    response = client.get("/api/locations?tags=red&tags=blue")

    assert response.status_code == 200
    assert response.json is not None
    uuids = {loc["uuid"] for loc in response.json}
    assert uuids == {
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    }


def test_get_locations_and_filter_mode_requires_every_selected_value():
    """An "and" category (e.g. amenities) narrows to entries that have every
    selected value, not just any of them - the opposite of "or"."""
    client = create_test_app(
        db_overrides={
            "categories": {"amenities": ["lighting", "benches", "toilets"]},
            "categories_filter_mode": {"amenities": "and"},
            "location_obligatory_fields": [("amenities", "list"), ("name", "str")],
            "data": [
                {
                    "name": "lighting-and-benches",
                    "position": [50, 50],
                    "amenities": ["lighting", "benches"],
                    "uuid": "11111111-1111-1111-1111-111111111111",
                },
                {
                    "name": "lighting-only",
                    "position": [60, 60],
                    "amenities": ["lighting"],
                    "uuid": "22222222-2222-2222-2222-222222222222",
                },
                {
                    "name": "benches-only",
                    "position": [70, 70],
                    "amenities": ["benches"],
                    "uuid": "33333333-3333-3333-3333-333333333333",
                },
            ],
            "visible_data": ["name", "amenities"],
        }
    )

    response = client.get("/api/locations?amenities=lighting&amenities=benches")

    assert response.status_code == 200
    assert response.json is not None
    uuids = {loc["uuid"] for loc in response.json}
    assert uuids == {"11111111-1111-1111-1111-111111111111"}


def test_get_locations_threshold_filter_mode():
    """A "threshold" category (e.g. speed limit) matches any stored value at or
    below the highest selected value."""
    client = create_test_app(
        db_overrides={
            "categories": {"speed_limit": ["10", "30", "50"]},
            "categories_filter_mode": {"speed_limit": "threshold"},
            "location_obligatory_fields": [("speed_limit", "str"), ("name", "str")],
            "data": [
                {
                    "name": "slow",
                    "position": [50, 50],
                    "speed_limit": "10",
                    "uuid": "11111111-1111-1111-1111-111111111111",
                },
                {
                    "name": "medium",
                    "position": [60, 60],
                    "speed_limit": "30",
                    "uuid": "22222222-2222-2222-2222-222222222222",
                },
                {
                    "name": "fast",
                    "position": [70, 70],
                    "speed_limit": "50",
                    "uuid": "33333333-3333-3333-3333-333333333333",
                },
            ],
            "visible_data": ["name", "speed_limit"],
        }
    )

    response = client.get("/api/locations?speed_limit=30")

    assert response.status_code == 200
    assert response.json is not None
    uuids = {loc["uuid"] for loc in response.json}
    assert uuids == {
        "11111111-1111-1111-1111-111111111111",
        "22222222-2222-2222-2222-222222222222",
    }


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("goodmap.formatter.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_get_location(test_app):
    response = test_app.get("/api/location/11111111-1111-1111-1111-111111111111")
    assert response.status_code == 200
    assert response.json == {
        "data": [
            ["name-translated", "test-translated"],
            ["test_category-translated", ["test-translated"]],
            ["type_of_place-translated", "test-place-translated"],
        ],
        "metadata": {"uuid-translated": "11111111-1111-1111-1111-111111111111-translated"},
        "position": [50.0, 50.0],
        "subtitle": "test-place-translated",
        "title": "test",
    }


def test_get_location_not_found(test_app):
    # Valid UUID that is absent from the fixture: routes through, then 404s.
    response = test_app.get("/api/location/99999999-9999-9999-9999-999999999999")
    assert response.status_code == 404
    assert response.json["message"] == "Location not found"


def test_get_location_rejects_non_uuid(test_app):
    """goodmap 2.0.0 accepts UUID location ids only; non-UUIDs 404 at routing."""
    response = test_app.get("/api/location/not-a-uuid")
    assert response.status_code == 404


# --- Report location tests ---


def test_reporting_location_success(test_app):
    response = api_post(
        test_app, "/api/report-location", {"id": "location-id", "description": "test issue 1"}
    )
    assert response.status_code == 200


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_reporting_returns_error_when_wrong_json(test_app):
    response = api_post(test_app, "/api/report-location", {"name": "location-id", "position": 50})
    assert response.status_code == 400
    assert response.json["message"] == "Invalid request data"


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_report_location_notification_success(test_app):
    response = api_post(
        test_app, "/api/report-location", {"id": "test-location", "description": "test issue 1"}
    )
    assert response.status_code == 200
    assert response.json["message"] == "Location reported-translated"


def test_report_location_with_invalid_json(test_app):
    response = test_app.post(
        "/api/report-location", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json["message"] == "Invalid request data"


def test_report_location_unexpected_error(test_app):
    db = test_app.application.db
    with mock.patch.object(db, "add_report", side_effect=Exception("Database failure")):
        response = api_post(
            test_app, "/api/report-location", {"id": "test-id", "description": "test issue 1"}
        )
        assert response.status_code == 500


# --- Report description validation tests ---


def test_report_description_matches_configured_option(test_app):
    """Description matching a configured issue option should be accepted."""
    response = api_post(
        test_app, "/api/report-location", {"id": "loc-1", "description": "test issue 1"}
    )
    assert response.status_code == 200


def test_report_description_not_in_options_without_other(test_app):
    """Description not in options (without 'other') should be rejected."""
    response = api_post(
        test_app, "/api/report-location", {"id": "loc-1", "description": "unknown problem"}
    )
    assert response.status_code == 400
    assert "Invalid report description" in response.json["message"]


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_report_description_free_text_with_other_option():
    """When 'other' is in options, free text within limit should be accepted."""
    test_app = create_test_app(db_overrides={"reported_issue_types": ["broken", "other"]})
    response = api_post(
        test_app, "/api/report-location", {"id": "loc-1", "description": "custom free text"}
    )
    assert response.status_code == 200


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_report_description_exceeds_max_length():
    """Description exceeding max length should be rejected even with 'other'."""
    test_app = create_test_app(db_overrides={"reported_issue_types": ["broken", "other"]})
    long_description = "x" * 501
    response = api_post(
        test_app, "/api/report-location", {"id": "loc-1", "description": long_description}
    )
    assert response.status_code in (400, 422)


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_report_description_empty_options_uses_fallback():
    """Empty issue options should fall back to defaults (which include 'other')."""
    test_app = create_test_app(db_overrides={"reported_issue_types": []})
    # "notHere" is in the default fallback list
    response = api_post(test_app, "/api/report-location", {"id": "loc-1", "description": "notHere"})
    assert response.status_code == 200


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_report_description_empty_options_allows_free_text():
    """Empty issue options fallback includes 'other', so free text is allowed."""
    test_app = create_test_app(db_overrides={"reported_issue_types": []})
    response = api_post(
        test_app, "/api/report-location", {"id": "loc-1", "description": "some custom text"}
    )
    assert response.status_code == 200


# --- Suggest location tests ---


def test_suggest_new_location_with_valid_data(test_app):
    response = multipart_suggest_post(
        test_app,
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


@pytest.mark.parametrize("scalar_looking_value", ["true", "false", "10", "null"])
def test_suggest_new_location_keeps_json_scalar_looking_field_as_string(
    test_app, scalar_looking_value
):
    """Regression test: a str-typed field whose value happens to look like a JSON
    scalar (e.g. a category literally named "true" or "10") must not be silently
    coerced into a bool/int/None. Since the whole suggestion travels as one JSON
    object, this only stays true because it's sent as a proper JSON string value
    (`json.dumps(value)`), not because of any per-field type sniffing.
    """
    db = test_app.application.db
    initial_count = len(db.get_suggestions({}))

    response = multipart_suggest_post(
        test_app,
        {
            "position": [50, 50],
            "name": "Test Organization",
            "type_of_place": scalar_looking_value,
            "test_category": ["test"],
        },
    )
    assert response.status_code == 200

    suggestions = db.get_suggestions({})
    assert len(suggestions) == initial_count + 1
    assert suggestions[-1]["type_of_place"] == scalar_looking_value


def test_suggest_new_location_keeps_json_array_looking_string_as_string(test_app):
    """A str-typed field whose value happens to look like valid JSON must stay a string."""
    db = test_app.application.db
    initial_count = len(db.get_suggestions({}))

    response = multipart_suggest_post(
        test_app,
        {
            "position": [50, 50],
            "name": '["not", "a", "list"]',
            "type_of_place": "shop",
            "test_category": ["test"],
        },
    )
    assert response.status_code == 200

    suggestions = db.get_suggestions({})
    assert len(suggestions) == initial_count + 1
    assert suggestions[-1]["name"] == '["not", "a", "list"]'
    assert suggestions[-1]["test_category"] == ["test"]


def test_suggest_location_accepts_photo_far_larger_than_the_form_fields(test_app):
    """A realistic photo is orders of magnitude bigger than the text fields around it.

    The request size cap has to be derived from attachment.max_size, not from the
    size of a suggestion's other fields, or every real photo would 413.
    """
    photo = JPEG_HEADER + b"\x00" * (500 * 1024)
    with mock.patch(
        "platzky.attachment.mime_validation.validate_content_mime_type", return_value=None
    ):
        response = multipart_suggest_post(
            test_app,
            {
                "position": [50, 50],
                "name": "Test Location",
                "type_of_place": "shop",
                "test_category": ["test"],
            },
            photo=(BytesIO(photo), "photo.jpg", "image/jpeg"),
        )

    assert response.status_code == 200


# --- Photo upload tests ---

# JPEG magic bytes header (enough for content-type detection)
JPEG_HEADER = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00"
FAKE_JPEG_CONTENT = JPEG_HEADER + b"\x00" * 100  # Minimal valid-looking JPEG


def test_suggest_location_with_valid_jpeg_photo(test_app):
    """Valid JPEG photo upload should succeed."""
    with mock.patch(
        "platzky.attachment.mime_validation.validate_content_mime_type", return_value=None
    ):
        response = multipart_suggest_post(
            test_app,
            {
                "position": [50, 50],
                "name": "Test Location",
                "type_of_place": "test-place",
                "test_category": ["test"],
            },
            photo=(BytesIO(FAKE_JPEG_CONTENT), "photo.jpg"),
        )
    assert response.status_code == 200
    assert response.json == {"message": "Location suggested"}


def test_suggest_location_rejects_png_photo(test_app):
    """PNG photos should be rejected (only JPEG allowed)."""
    response = multipart_suggest_post(
        test_app,
        {
            "position": [50, 50],
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": ["test"],
        },
        photo=(BytesIO(b"fake png content"), "photo.png"),
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]
    assert "jpeg" in response.json["message"].lower()


def test_suggest_location_rejects_wrong_extension(test_app):
    """File with disallowed extension should be rejected."""
    response = multipart_suggest_post(
        test_app,
        {
            "position": [50, 50],
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": ["test"],
        },
        photo=(BytesIO(FAKE_JPEG_CONTENT), "photo.gif"),
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]


def test_suggest_location_rejects_oversized_photo(test_app):
    """Photos over 5 MiB should be rejected."""
    oversized_content = JPEG_HEADER + (b"\x00" * (5 * 1024 * 1024 + 1))

    response = multipart_suggest_post(
        test_app,
        {
            "position": [50, 50],
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": ["test"],
        },
        photo=(BytesIO(oversized_content), "photo.jpg"),
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]
    assert "5MiB" in response.json["message"]


def test_suggest_location_rejects_fake_jpeg(test_app):
    """Text file claiming to be JPEG should be rejected by content validation."""
    fake_jpeg = b"This is not a JPEG file, just plain text"

    response = multipart_suggest_post(
        test_app,
        {
            "position": [50, 50],
            "name": "Test Location",
            "type_of_place": "test-place",
            "test_category": ["test"],
        },
        photo=(BytesIO(fake_jpeg), "photo.jpg"),
    )
    assert response.status_code == 400
    assert "Invalid photo" in response.json["message"]


def test_suggest_location_with_photo_stores_suggestion(test_app):
    """Verify that location with photo is stored in database."""
    db = test_app.application.db
    initial_count = len(db.get_suggestions({}))

    with mock.patch(
        "platzky.attachment.mime_validation.validate_content_mime_type", return_value=None
    ):
        response = multipart_suggest_post(
            test_app,
            {
                "position": [50, 50],
                "name": "Test Location With Photo",
                "type_of_place": "test-place",
                "test_category": ["test"],
            },
            photo=(BytesIO(FAKE_JPEG_CONTENT), "photo.jpg"),
        )
    assert response.status_code == 200

    # Verify suggestion was stored
    suggestions = db.get_suggestions({})
    assert len(suggestions) == initial_count + 1
    assert suggestions[-1]["name"] == "Test Location With Photo"


def test_suggest_location_without_photo_notifies_with_empty_frozenset():
    """Regression test for a production crash: notifier plugins (e.g. platzky_sendmail)
    call list(notification.attachments) unconditionally, so attachments must always be
    an iterable frozenset, never None, when no photo is attached.

    Engine.notify must be patched before the app is created, since notifier_function
    captures the bound method at app-factory time.
    """
    with mock.patch("platzky.engine.Engine.notify") as mock_notify:
        app = create_test_app()
        response = multipart_suggest_post(
            app,
            {
                "uuid": "one",
                "name": "Test Organization",
                "type_of_place": "type",
                "test_category": ["test"],
                "position": [50, 50],
            },
        )

    assert response.status_code == 200
    _, kwargs = mock_notify.call_args
    assert kwargs["attachments"] == frozenset()


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
    response = multipart_suggest_post(test_app, data)
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
    response = test_app.post(
        "/api/suggest-new-point",
        data={"location": body},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.json["message"] == expected_message


def test_suggest_new_location_with_list_item_too_long(test_app):
    long_item = "x" * 101
    response = multipart_suggest_post(
        test_app,
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
        response = multipart_suggest_post(
            test_app,
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
        ("position", {"a": {"b": {"c": "d"}}}, "too complex"),  # deeply nested object
        ("position", [[["deeply", "nested"]]], "too complex"),  # deeply nested array
        ("position", ["x" * (55 * 1024)], "too large"),  # oversized payload
    ],
)
def test_suggest_location_dos_protection(test_app, field_name, malicious_value, error_substring):
    response = multipart_suggest_post(
        test_app,
        {
            "name": "Test",
            field_name: malicious_value,
            "test_category": ["test"],
            "type_of_place": "test-place",
        },
    )
    assert response.status_code == 400
    data = response.json
    assert error_substring in data["message"].lower()


def test_suggest_location_dos_protection_deeply_nested_location_field(test_app):
    response = test_app.post(
        "/api/suggest-new-point",
        data={"location": '{"a":{"b":{"c":"d"}}}'},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    data = response.json
    assert "too complex" in data["message"].lower()


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
    "zoom,expected_status",
    [
        ("invalid", 400),
        ("-1", 400),
        ("17", 400),
        ("0", 200),
        ("16", 200),
    ],
)
def test_location_clustering_zoom_validation(test_app, zoom, expected_status):
    response = test_app.get(f"/api/locations-clustered?zoom={zoom}")
    assert response.status_code == expected_status
    if expected_status == 400:
        assert response.json["message"] == "Invalid request data"
        assert "zoom" in response.json["error"]


def test_location_clustering_empty_locations():
    test_app = create_test_app(db_overrides={"data": []})
    response = test_app.get("/api/locations-clustered?zoom=10")
    assert response.status_code == 200
    assert response.json == []


def test_location_clustering_exception_handling(test_app):
    with mock.patch(
        "goodmap.api.core_api.pysupercluster.SuperCluster",
        side_effect=Exception("Clustering failed"),
    ):
        response = test_app.get("/api/locations-clustered?zoom=10")
        assert response.status_code == 500
        assert "An error occurred during clustering" in response.json["message"]


def test_location_clustering_logs_on_invalid_parameter(test_app):
    """The rejected value itself goes to the log, not to the caller."""
    with mock.patch("goodmap.api.core_api.logger") as mock_logger:
        test_app.get("/api/locations-clustered?zoom=invalid")
        mock_logger.warning.assert_called_once()
        assert "Request validation failed" in mock_logger.warning.call_args[0][0]


def test_location_clustering_logs_on_exception(test_app):
    with (
        mock.patch(
            "goodmap.api.core_api.pysupercluster.SuperCluster",
            side_effect=Exception("Clustering failed"),
        ),
        mock.patch("goodmap.api.core_api.logger") as mock_logger,
    ):
        test_app.get("/api/locations-clustered?zoom=10")
        mock_logger.exception.assert_called_once()
        assert "Clustering operation failed" in mock_logger.exception.call_args[0][0]


# --- Helper function tests ---


@mock.patch("goodmap.api.core_api.gettext", fake_translation)
def test_make_tuple_translation():
    keys = ["alpha", "beta"]
    assert make_tuple_translation(keys) == [
        ("alpha", "alpha-translated"),
        ("beta", "beta-translated"),
    ]


def test_issue_options_from_db(test_app):
    db = test_app.application.db
    assert db.get_issue_options() == ["test issue 1", "test issue 2"]


def test_issue_options_empty_when_not_configured():
    client = create_test_app(db_overrides={"reported_issue_types": []})
    db = client.application.db  # type: ignore[attr-defined]
    assert db.get_issue_options() == []


def test_issue_options_defaults_to_empty_when_missing():
    config_data = get_test_config_data()
    config_data["FEATURE_FLAGS"] = {
        "CATEGORIES_HELP": True,
        "USE_LAZY_LOADING": True,
        "ENABLE_ADMIN_PANEL": True,
    }
    config_data["DB"]["DATA"].pop("reported_issue_types", None)
    config = GoodmapConfig.model_validate(config_data)
    app = create_app_from_config(config)
    db = app.db
    assert db.get_issue_options() == []  # type: ignore[attr-defined]


def test_get_locations_from_request_helper(test_app):
    from goodmap.api.core_api import get_locations_from_request

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

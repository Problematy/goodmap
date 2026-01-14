import json
from typing import Any
from unittest import mock

import deprecation
import pytest

from goodmap.config import GoodmapConfig
from goodmap.core_api import get_or_none, make_tuple_translation
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
        feature_flags = {"CATEGORIES_HELP": True, "USE_LAZY_LOADING": True}
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


def test_api_doc_redirect(test_app):
    response = test_app.get("/api/doc")
    assert response.status_code == 302
    assert "/api/doc/swagger/" in response.headers["Location"]


# --- Categories endpoint tests ---


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_endpoint_returns_categories(test_app):
    response = test_app.get("/api/categories")
    assert response.status_code == 200
    assert response.json == {
        "categories": [["test-category", "test-category-translated"]],
        "categories_help": [{"test-category": "categories_help_test-category-translated"}],
    }


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_endpoint_returns_categories_old_way(test_app_without_helpers):
    response = test_app_without_helpers.get("/api/categories")
    assert response.status_code == 200
    assert response.json == [["test-category", "test-category-translated"]]


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_getting_all_category_data(test_app):
    response = test_app.get("/api/category/test-category")
    assert response.status_code == 200
    assert response.json == {
        "categories_options": [["test", "test-translated"], ["test2", "test2-translated"]],
        "categories_options_help": [{"test": "categories_options_help_test-translated"}],
    }


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_getting_all_category_data_old_way(test_app_without_helpers):
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


# --- Admin location tests ---


@mock.patch("goodmap.core_api.uuid.uuid4")
def test_admin_post_location_success(mock_uuid4, test_app):
    from uuid import UUID

    mock_uuid4.return_value = UUID("00000000-0000-0000-0000-000000000001")
    data = {
        "uuid": None,
        "name": "LocName",
        "type_of_place": "Type",
        "test_category": ["cat"],
        "position": [10.0, 20.0],
        "remark": "some comment",
    }
    response = api_post(test_app, "/api/admin/locations", data)
    assert response.status_code == 200
    resp_json = response.json
    assert resp_json["name"] == "LocName"
    assert resp_json["type_of_place"] == "Type"
    assert resp_json["test_category"] == ["cat"]
    assert resp_json["position"] == [10.0, 20.0]
    assert isinstance(resp_json["uuid"], str)


@pytest.mark.parametrize(
    "data,expected_message",
    [
        ({}, "Invalid location data"),
        ({"position": "bad"}, "Invalid location data"),
        (
            {
                "name": "Test",
                "type_of_place": "Test",
                "test_category": ["test"],
                "position": "invalid",
            },
            None,
        ),
    ],
)
def test_admin_post_location_invalid_data(test_app, data, expected_message):
    response = api_post(test_app, "/api/admin/locations", data)
    assert response.status_code == 400
    if expected_message:
        assert expected_message in response.json["message"]


@pytest.mark.parametrize(
    "body,expected_message",
    [
        ("null", "Invalid request data"),
        ("invalid json", None),
    ],
)
def test_admin_post_location_malformed_body(test_app, body, expected_message):
    response = test_app.post("/api/admin/locations", data=body, content_type="application/json")
    assert response.status_code == 400
    if expected_message:
        assert response.json["message"] == expected_message


def test_admin_put_location_success(test_app):
    # Create a location first
    create_data = {
        "name": "OriginalName",
        "type_of_place": "OriginalType",
        "test_category": ["original"],
        "position": [0.0, 0.0],
        "remark": "original comment",
    }
    create_response = api_post(test_app, "/api/admin/locations", create_data)
    assert create_response.status_code == 200
    location_id = create_response.json["uuid"]

    # Update it
    update_data = {
        "uuid": None,
        "name": "NewName",
        "type_of_place": "NewType",
        "test_category": ["new"],
        "position": [1.0, 2.0],
        "remark": "some comments",
    }
    response = api_put(test_app, f"/api/admin/locations/{location_id}", update_data)
    assert response.status_code == 200
    resp_json = response.json
    assert resp_json["name"] == "NewName"
    assert resp_json["type_of_place"] == "NewType"
    assert resp_json["test_category"] == ["new"]
    assert resp_json["position"] == [1.0, 2.0]
    assert resp_json["uuid"] == location_id


@pytest.mark.parametrize(
    "data",
    [
        {"position": "bad"},
        {
            "name": "NewName",
            "type_of_place": "NewType",
            "test_category": ["new"],
            "position": "invalid",
        },
        {"invalid": "data"},
    ],
)
def test_admin_put_location_invalid_data(test_app, data):
    response = api_put(test_app, "/api/admin/locations/loc123", data)
    assert response.status_code == 400


def test_admin_put_location_null_json_body(test_app):
    response = test_app.put(
        "/api/admin/locations/some-uuid", data="null", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json["message"] == "Invalid request data"


def test_admin_put_location_invalid_json(test_app):
    response = test_app.put(
        "/api/admin/locations/test-id", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 400


def test_admin_delete_location_success(test_app):
    # Create a location first
    create_data = {
        "name": "ToDeleteName",
        "type_of_place": "ToDeleteType",
        "test_category": ["delete"],
        "position": [0.0, 0.0],
        "remark": "will be deleted",
    }
    create_response = api_post(test_app, "/api/admin/locations", create_data)
    assert create_response.status_code == 200
    location_id = create_response.json["uuid"]

    response = api_delete(test_app, f"/api/admin/locations/{location_id}")
    assert response.status_code == 204
    assert response.data == b""


def test_admin_delete_location_not_found(test_app):
    response = api_delete(test_app, "/api/admin/locations/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json["message"].lower()


# --- Admin pagination tests ---


@pytest.mark.parametrize(
    "endpoint", ["/api/admin/locations", "/api/admin/suggestions", "/api/admin/reports"]
)
def test_admin_pagination_structure(test_app, endpoint):
    response = test_app.get(f"{endpoint}?page=1&per_page=10")
    assert response.status_code == 200
    data = response.json
    assert "pagination" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    pagination = data["pagination"]
    assert pagination["page"] == 1
    assert pagination["per_page"] == 10
    for key in ["total", "page", "per_page", "total_pages"]:
        assert key in pagination


def test_admin_pagination_edge_cases(test_app):
    # Invalid page defaults to 1
    response = test_app.get("/api/admin/locations?page=invalid&per_page=10")
    assert response.status_code == 200
    assert response.json["pagination"]["page"] == 1

    # Invalid per_page defaults to 20
    response = test_app.get("/api/admin/locations?page=1&per_page=invalid")
    assert response.status_code == 200
    assert response.json["pagination"]["per_page"] == 20

    # per_page="all" returns single page
    response = test_app.get("/api/admin/locations?page=1&per_page=all")
    assert response.status_code == 200
    assert response.json["pagination"]["total_pages"] == 1


@pytest.mark.parametrize(
    "endpoint,params",
    [
        ("/api/admin/locations", "sort_by=name&sort_order=desc"),
        ("/api/admin/suggestions", "status=pending&sort_by=created_at&sort_order=desc"),
        ("/api/admin/reports", "sort_by=created_at&sort_order=asc"),
    ],
)
def test_admin_sorting(test_app, endpoint, params):
    response = test_app.get(f"{endpoint}?{params}")
    assert response.status_code == 200


# --- Admin suggestion tests ---


@pytest.mark.parametrize(
    "status,expected_code",
    [
        ("bad", 422),
        ("invalid_status", 422),
    ],
)
def test_admin_put_suggestion_invalid_status(test_app, status, expected_code):
    response = api_put(test_app, "/api/admin/suggestions/s1", {"status": status})
    assert response.status_code == expected_code
    assert isinstance(response.json, list)


def test_admin_put_suggestion_not_found(test_app):
    response = api_put(test_app, "/api/admin/suggestions/nonexistent", {"status": "accepted"})
    assert response.status_code == 404
    assert "not found" in response.json["message"].lower()


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_admin_suggestion_processing(test_app):
    """Test suggestion processing: already processed and successful scenarios."""
    test_app.application.db.data["suggestions"] = [
        {"uuid": "already-processed", "status": "accepted", "name": "test"},
        {"uuid": "pending-one", "status": "pending", "name": "test2"},
    ]

    # Already processed returns 409
    response = api_put(test_app, "/api/admin/suggestions/already-processed", {"status": "rejected"})
    assert response.status_code == 409
    assert "Suggestion already processed" in response.json["message"]

    # Pending one can be processed
    response = api_put(test_app, "/api/admin/suggestions/pending-one", {"status": "rejected"})
    assert response.status_code == 200
    assert test_app.application.db.get_suggestion("pending-one")["status"] == "rejected"


def test_admin_suggestion_processing_location_validation_error(test_app):
    """Test LocationValidationError when accepting suggestion with invalid data."""
    db = test_app.application.db
    db.data["suggestions"].append(
        {
            "uuid": "invalid-suggestion",
            "name": "Invalid",
            "type_of_place": "test",
            "test_category": ["test"],
            "position": [200, 200],  # Invalid coordinates
            "status": "pending",
        }
    )

    response = api_put(
        test_app, "/api/admin/suggestions/invalid-suggestion", {"status": "accepted"}
    )
    assert response.status_code == 400
    assert "Invalid location data" in response.json["message"]


def test_admin_suggestion_processing_duplicate_location(test_app):
    """Test LocationAlreadyExistsError when accepting suggestion with duplicate UUID."""
    db = test_app.application.db
    db.data["data"].append(
        {
            "uuid": "duplicate-uuid",
            "name": "Existing",
            "position": [50, 50],
            "test_category": ["test"],
            "type_of_place": "test",
        }
    )
    db.data["suggestions"].append(
        {
            "uuid": "duplicate-uuid",
            "name": "Suggested",
            "type_of_place": "test",
            "test_category": ["test"],
            "position": [60, 60],
            "status": "pending",
        }
    )

    response = api_put(test_app, "/api/admin/suggestions/duplicate-uuid", {"status": "accepted"})
    assert response.status_code == 409
    assert "Location already exists" in response.json["message"]


# --- Admin report tests ---


@pytest.mark.parametrize(
    "data,expected_code",
    [
        ({"status": "bad"}, 422),
        ({"priority": "bad"}, 422),
    ],
)
def test_admin_put_report_invalid_data(test_app, data, expected_code):
    response = api_put(test_app, "/api/admin/reports/r1", data)
    assert response.status_code == expected_code
    assert isinstance(response.json, list)


def test_admin_put_report_not_found(test_app):
    response = api_put(test_app, "/api/admin/reports/nonexistent", {"status": "resolved"})
    assert response.status_code == 404
    assert "Report not found" in response.json["message"]


def test_admin_put_report_invalid_json(test_app):
    response = test_app.put(
        "/api/admin/reports/test-id", data="invalid json", content_type="application/json"
    )
    assert response.status_code == 400


def test_admin_report_update_race_condition(test_app):
    """Test ReportNotFoundError handler for race condition scenario."""
    from goodmap.exceptions import ReportNotFoundError

    db = test_app.application.db
    with (
        mock.patch.object(
            db, "get_report", return_value={"uuid": "race-uuid", "status": "pending"}
        ),
        mock.patch.object(db, "update_report", side_effect=ReportNotFoundError("race-uuid")),
    ):
        response = api_put(test_app, "/api/admin/reports/race-uuid", {"status": "resolved"})
        assert response.status_code == 404
        assert "Report not found" in response.json["message"]


# --- Database exception tests ---


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_admin_database_exceptions(test_app):
    """Test database exceptions in admin endpoints."""
    db = test_app.application.db
    valid_location = {
        "name": "Test",
        "position": [50, 50],
        "test_category": ["test"],
        "type_of_place": "test",
    }

    # POST location exception
    with mock.patch.object(db, "add_location", side_effect=Exception("Database error")):
        response = api_post(test_app, "/api/admin/locations", valid_location)
        assert response.status_code == 500

    # PUT location exception
    with mock.patch.object(db, "update_location", side_effect=Exception("Update error")):
        response = api_put(test_app, "/api/admin/locations/test-id", valid_location)
        assert response.status_code == 500

    # DELETE location exception
    with mock.patch.object(db, "delete_location", side_effect=Exception("Delete error")):
        response = api_delete(test_app, "/api/admin/locations/test-id")
        assert response.status_code == 500

    # Suggestion update exception
    with (
        mock.patch.object(
            db,
            "get_suggestion",
            return_value={
                "uuid": "test-uuid",
                "status": "pending",
                "name": "test",
                "position": [50, 50],
                "test_category": ["test"],
                "type_of_place": "test",
            },
        ),
        mock.patch.object(db, "add_location", return_value=None),
        mock.patch.object(db, "update_suggestion", side_effect=Exception("Suggestion error")),
    ):
        response = api_put(test_app, "/api/admin/suggestions/test-id", {"status": "accepted"})
        assert response.status_code == 500

    # Successful report update
    with (
        mock.patch.object(
            db, "get_report", return_value={"status": "pending", "priority": "medium"}
        ),
        mock.patch.object(db, "update_report", return_value=None),
    ):
        response = api_put(test_app, "/api/admin/reports/test-id", {"status": "resolved"})
        assert response.status_code == 200

    # Report update ValueError exception
    with (
        mock.patch.object(
            db, "get_report", return_value={"status": "pending", "priority": "medium"}
        ),
        mock.patch.object(db, "update_report", side_effect=ValueError("Report error")),
    ):
        response = api_put(test_app, "/api/admin/reports/test-id2", {"status": "resolved"})
        assert response.status_code == 500


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
        # as_basic_info=False returns Location objects
        locations = get_locations_from_request(
            test_app.application.db, mock_request_args, as_basic_info=False
        )
        assert isinstance(locations, list)
        if locations:
            assert hasattr(locations[0], "basic_info")

        # as_basic_info=True returns dicts
        locations = get_locations_from_request(
            test_app.application.db, mock_request_args, as_basic_info=True
        )
        assert isinstance(locations, list)
        if locations:
            assert isinstance(locations[0], dict)
            assert "uuid" in locations[0]
            assert "position" in locations[0]

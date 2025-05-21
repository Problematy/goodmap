import json
from unittest import mock
from unittest.mock import MagicMock

import pytest
from flask import Flask
from platzky.config import LanguageConfig, Languages, languages_dict

from goodmap.core_api import core_pages
from goodmap.data_models.location import LocationBase, create_location_model


def fake_translation(key: str):
    return f"{key}-translated"


@pytest.fixture
def notifier_function():
    return MagicMock()


@pytest.fixture
def db_mock():
    return MagicMock()


@pytest.fixture
def test_app(notifier_function, db_mock):
    CustomLocation = create_location_model(
        [("test_category", list[str]), ("type_of_place", str), ("name", str)]
    )
    language_config = LanguageConfig(name="English", flag="uk", country="GB")
    languages = languages_dict(Languages({"en": language_config}))
    app = Flask(__name__)
    db_mock.get_data.return_value = {
        "categories": {"test-category": ["test", "test2"]},
        "locations": [],
        "data": [
            {
                "name": "test",
                "position": [50, 50],
                "test-category": ["test"],
                "type_of_place": "test-place",
                "uuid": "1",
            },
            {
                "name": "test2",
                "position": [60, 60],
                "test-category": ["second-category"],
                "type_of_place": "test-place2",
                "uuid": "2",
            },
        ],
        "meta_data": ["uuid"],
        "visible_data": ["name", "test_category", "type_of_place"],
    }
    db_mock.get_locations.return_value = [
        LocationBase(position=(50, 50), uuid="1"),
        LocationBase(position=(60, 60), uuid="2"),
    ]

    db_mock.get_location.return_value = CustomLocation(
        position=(50, 50), uuid="1", test_category=["test"], type_of_place="test-place", name="test"
    )

    app.register_blueprint(
        core_pages(
            db_mock, languages, notifier_function, lambda: "csrf", location_model=CustomLocation
        )
    )
    return app.test_client()


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_reporting_location_is_sending_message_with_name_and_position(
    test_app, notifier_function, db_mock
):
    data = {"id": "location-id", "description": "some error"}
    headers = {"Content-Type": "application/json"}
    response = test_app.post("/api/report-location", data=json.dumps(data), headers=headers)
    notification_message = str(notifier_function.call_args)

    assert "id" in notification_message
    assert "some error" in notification_message
    assert response.status_code == 200
    # Stored in database
    assert db_mock.add_report.called, "add_report should be called"
    report_arg = db_mock.add_report.call_args[0][0]
    assert report_arg.get("location_id") == "location-id"
    assert report_arg.get("description") == "some error"
    assert report_arg.get("status") == "pending"
    assert report_arg.get("priority") == "medium"
    assert isinstance(report_arg.get("uuid"), str)


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_reporting_returns_error_when_wrong_json(test_app, notifier_function, db_mock):
    data = {"name": "location-id", "position": 50}
    headers = {"Content-Type": "application/json"}
    response = test_app.post("/api/report-location", data=json.dumps(data), headers=headers)
    assert response.status_code == 400
    # No report stored
    assert not db_mock.add_report.called
    assert "Error" in response.json["message"]


def test_language_endpoint_returns_languages(test_app):
    response = test_app.get("/api/languages")
    assert response.status_code == 200
    # TODO domain should not be in response if its None
    assert response.json == {
        "en": {"country": "GB", "domain": None, "flag": "uk", "name": "English"}
    }


# TODO change db_mock of below tests to real json db


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_endpoint_returns_categories(test_app):
    # make gettext used in flask_babel return the same string as the input
    response = test_app.get("/api/categories")
    assert response.status_code == 200
    assert response.json == [["test-category", "test-category-translated"]]


@mock.patch("importlib.metadata.version", return_value="0.1.2")
def test_version_endpoint_returns_version(mock_returning_version, test_app):
    response = test_app.get("/api/version")
    mock_returning_version.assert_called_once_with("goodmap")
    assert response.status_code == 200
    assert response.json == {"backend": "0.1.2"}


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_getting_all_category_data(test_app):
    response = test_app.get("/api/category/test-category")
    assert response.status_code == 200
    assert response.json == [["test", "test-translated"], ["test2", "test2-translated"]]


def test_getting_token(test_app):
    response = test_app.get("/api/generate-csrf-token")
    assert response.status_code == 200
    assert "csrf_token" in response.json
    assert response.json["csrf_token"] == "csrf"


def test_suggest_new_location_with_valid_data(test_app, db_mock):
    response = test_app.post(
        "/api/suggest-new-point",
        data=json.dumps(
            {
                "uuid": "one",
                "name": "Test Organization",
                "type_of_place": "type",
                "test_category": ["test"],
                "position": [50, 50],
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.get_json() == {"message": "Location suggested"}
    # Stored in database
    assert db_mock.add_suggestion.called, "add_suggestion should be called"
    sugg_arg = db_mock.add_suggestion.call_args[0][0]
    # All fields and a uuid were stored
    assert sugg_arg.get("name") == "Test Organization"
    assert sugg_arg.get("type_of_place") == "type"
    assert sugg_arg.get("test_category") == ["test"]
    assert sugg_arg.get("position") == [50, 50] or tuple(sugg_arg.get("position")) == (50, 50)
    assert isinstance(sugg_arg.get("uuid"), str)


def test_suggest_new_location_without_required_fields(test_app, db_mock):
    response = test_app.post(
        "/api/suggest-new-point",
        data=json.dumps({"photo": "Test Photo"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not db_mock.add_suggestion.called


def test_suggest_new_location_with_empty_data(test_app, db_mock):
    response = test_app.post(
        "/api/suggest-new-point",
        data=json.dumps({}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not db_mock.add_suggestion.called


def test_suggest_new_location_with_invalid_data(test_app, db_mock):
    response = test_app.post(
        "/api/suggest-new-point",
        data=json.dumps({"name": 123, "position": 456, "photo": "Test Photo"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert not db_mock.add_suggestion.called


def test_suggest_new_location_with_error_during_sending_notification(test_app, notifier_function):
    notifier_function.side_effect = Exception("Test Error")
    response = test_app.post(
        "/api/suggest-new-point",
        data=json.dumps(
            {
                "name": "Test Organization",
                "type_of_place": "type",
                "test_category": ["test"],
                "position": [50, 50],
                "photo": "Test Photo",
            }
        ),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.get_json() == {"message": "Error sending notification : Test Error"}


def test_get_locations(test_app):
    response = test_app.get("/api/locations")
    assert response.status_code == 200
    assert response.json == [
        {"uuid": "1", "position": [50, 50]},
        {"uuid": "2", "position": [60, 60]},
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


# Tests for admin endpoints


@mock.patch("goodmap.core_api.uuid.uuid4")
def test_admin_post_location_success(mock_uuid4, test_app, db_mock):
    from uuid import UUID

    mock_uuid4.return_value = UUID("00000000-0000-0000-0000-000000000001")
    data = {
        "name": "LocName",
        "type_of_place": "Type",
        "test_category": ["cat"],
        "position": [10.0, 20.0],
    }
    response = test_app.post(
        "/api/admin/locations", data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200
    resp_json = response.json
    expected = data.copy()
    expected["uuid"] = str(mock_uuid4.return_value)
    assert resp_json == expected
    # add_location should be called with model_dump dict (position as tuple)
    called_args, _ = db_mock.add_location.call_args
    payload = called_args[0]
    # position should be a tuple in the payload
    assert isinstance(payload.get("position"), tuple)
    assert payload.get("position") == tuple(data["position"])
    # other fields should match
    for key in ("uuid", "name", "type_of_place", "test_category"):
        assert payload.get(key) == expected.get(key)


def test_admin_post_location_invalid_data(test_app, db_mock):
    response = test_app.post(
        "/api/admin/locations", data=json.dumps({}), content_type="application/json"
    )
    assert response.status_code == 400
    assert "Invalid location data" in response.json["message"]


@mock.patch("goodmap.core_api.uuid.uuid4")
def test_admin_post_location_error(mock_uuid4, test_app, db_mock):
    from uuid import UUID

    mock_uuid4.return_value = UUID("00000000-0000-0000-0000-000000000002")
    db_mock.add_location.side_effect = Exception("DB error")
    data = {
        "name": "LocName",
        "type_of_place": "Type",
        "test_category": ["cat"],
        "position": [10.0, 20.0],
    }
    response = test_app.post(
        "/api/admin/locations", data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json["message"] == "Error creating location: DB error"


def test_admin_put_location_success(test_app, db_mock):
    data = {
        "name": "NewName",
        "type_of_place": "NewType",
        "test_category": ["new"],
        "position": [1.0, 2.0],
    }
    location_id = "loc123"
    response = test_app.put(
        f"/api/admin/locations/{location_id}",
        data=json.dumps(data),
        content_type="application/json",
    )
    assert response.status_code == 200
    expected = data.copy()
    expected["uuid"] = location_id
    assert response.json == expected
    # update_location should be called with tuple position
    called_args, _ = db_mock.update_location.call_args
    assert called_args[0] == location_id
    payload = called_args[1]
    assert isinstance(payload.get("position"), tuple)
    assert payload.get("position") == tuple(data["position"])
    for key in ("uuid", "name", "type_of_place", "test_category"):
        assert payload.get(key) == expected.get(key)


def test_admin_put_location_invalid_data(test_app, db_mock):
    response = test_app.put(
        "/api/admin/locations/loc123",
        data=json.dumps({"position": "bad"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Invalid location data" in response.json["message"]


def test_admin_put_location_error(test_app, db_mock):
    db_mock.update_location.side_effect = Exception("Update error")
    data = {
        "name": "NewName",
        "type_of_place": "NewType",
        "test_category": ["new"],
        "position": [1.0, 2.0],
    }
    response = test_app.put(
        "/api/admin/locations/loc123", data=json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 400
    assert response.json["message"] == "Error updating location: Update error"


def test_admin_delete_location_success(test_app, db_mock):
    location_id = "loc123"
    response = test_app.delete(f"/api/admin/locations/{location_id}")
    assert response.status_code == 204
    assert response.data == b""
    db_mock.delete_location.assert_called_once_with(location_id)


def test_admin_delete_location_not_found(test_app, db_mock):
    db_mock.delete_location.side_effect = ValueError("No such id")
    response = test_app.delete("/api/admin/locations/notexist")
    assert response.status_code == 404
    assert "Location not found" in response.json["message"]


def test_admin_delete_location_error(test_app, db_mock):
    db_mock.delete_location.side_effect = Exception("Delete error")
    response = test_app.delete("/api/admin/locations/loc123")
    assert response.status_code == 400
    assert response.json["message"] == "Error deleting location: Delete error"


def test_admin_put_suggestion_invalid_status(test_app, db_mock):
    response = test_app.put(
        "/api/admin/suggestions/s1",
        data=json.dumps({"status": "bad"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Invalid status: bad" in response.json["message"]


def test_admin_put_suggestion_not_found(test_app, db_mock):
    db_mock.get_suggestion.return_value = None
    response = test_app.put(
        "/api/admin/suggestions/s1",
        data=json.dumps({"status": "accepted"}),
        content_type="application/json",
    )
    assert response.status_code == 404
    assert "Suggestion not found" in response.json["message"]


def test_admin_put_suggestion_already_processed(test_app, db_mock):
    db_mock.get_suggestion.return_value = {"status": "accepted"}
    response = test_app.put(
        "/api/admin/suggestions/s1",
        data=json.dumps({"status": "rejected"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Suggestion already processed" in response.json["message"]


def test_admin_put_suggestion_accept(test_app, db_mock):
    suggestion_initial = {
        "id": "s1",
        "status": "pending",
        "name": "loc",
        "position": [1, 2],
        "photo": "p",
    }
    suggestion_updated = {
        "id": "s1",
        "status": "accepted",
        "name": "loc",
        "position": [1, 2],
        "photo": "p",
    }
    db_mock.get_suggestion.side_effect = [suggestion_initial, suggestion_updated]
    response = test_app.put(
        "/api/admin/suggestions/s1",
        data=json.dumps({"status": "accepted"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json == suggestion_updated
    db_mock.add_location.assert_called_once_with(
        {k: v for k, v in suggestion_initial.items() if k != "status"}
    )
    db_mock.update_suggestion.assert_called_once_with("s1", "accepted")


def test_admin_put_suggestion_reject(test_app, db_mock):
    suggestion_initial = {
        "id": "s1",
        "status": "pending",
        "name": "loc",
        "position": [1, 2],
        "photo": "p",
    }
    suggestion_updated = {
        "id": "s1",
        "status": "rejected",
        "name": "loc",
        "position": [1, 2],
        "photo": "p",
    }
    db_mock.get_suggestion.side_effect = [suggestion_initial, suggestion_updated]
    response = test_app.put(
        "/api/admin/suggestions/s1",
        data=json.dumps({"status": "rejected"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json == suggestion_updated
    assert not db_mock.add_location.called
    db_mock.update_suggestion.assert_called_once_with("s1", "rejected")


def test_admin_put_report_invalid_status(test_app, db_mock):
    response = test_app.put(
        "/api/admin/reports/r1", data=json.dumps({"status": "bad"}), content_type="application/json"
    )
    assert response.status_code == 400
    assert "Invalid status: bad" in response.json["message"]


def test_admin_put_report_invalid_priority(test_app, db_mock):
    response = test_app.put(
        "/api/admin/reports/r1",
        data=json.dumps({"priority": "bad"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Invalid priority: bad" in response.json["message"]


def test_admin_put_report_not_found(test_app, db_mock):
    db_mock.get_report.return_value = None
    response = test_app.put(
        "/api/admin/reports/r1",
        data=json.dumps({"status": "resolved"}),
        content_type="application/json",
    )
    assert response.status_code == 404
    assert "Report not found" in response.json["message"]


def test_admin_put_report_success(test_app, db_mock):
    report_initial = {"id": "r1", "status": "pending", "priority": "medium"}
    report_updated = {"id": "r1", "status": "resolved", "priority": "critical"}
    db_mock.get_report.side_effect = [report_initial, report_updated]
    response = test_app.put(
        "/api/admin/reports/r1",
        data=json.dumps({"status": "resolved", "priority": "critical"}),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json == report_updated
    db_mock.update_report.assert_called_once_with("r1", status="resolved", priority="critical")


def test_admin_get_locations_pagination(test_app, db_mock):
    # Simulate 3 locations for pagination
    from goodmap.data_models.location import LocationBase

    items = [
        LocationBase(position=(0, 0), uuid="a"),
        LocationBase(position=(1, 1), uuid="b"),
        LocationBase(position=(2, 2), uuid="c"),
    ]
    db_mock.get_locations.return_value = items
    response = test_app.get("/api/admin/locations?page=2&per_page=1")
    assert response.status_code == 200
    data = response.json
    assert data["total"] == 3
    assert data["page"] == 2
    assert data["per_page"] == 1
    assert data["total_pages"] == 3
    assert isinstance(data["items"], list) and len(data["items"]) == 1
    assert data["items"][0]["uuid"] == "b"


def test_admin_get_suggestions_pagination(test_app, db_mock):
    # Simulate 2 suggestions
    suggestions = [
        {"uuid": "s1", "status": "pending"},
        {"uuid": "s2", "status": "accepted"},
    ]
    db_mock.get_suggestions.return_value = suggestions
    response = test_app.get("/api/admin/suggestions?page=1&per_page=1")
    assert response.status_code == 200
    data = response.json
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["per_page"] == 1
    assert data["total_pages"] == 2
    assert data["items"] == [suggestions[0]]


def test_admin_get_reports_pagination(test_app, db_mock):
    # Simulate 2 reports
    reports = [
        {"id": "r1", "status": "pending", "priority": "low"},
        {"id": "r2", "status": "resolved", "priority": "high"},
    ]
    db_mock.get_reports.return_value = reports
    response = test_app.get("/api/admin/reports?page=2&per_page=1")
    assert response.status_code == 200
    data = response.json
    assert data["total"] == 2
    assert data["page"] == 2
    assert data["per_page"] == 1
    assert data["total_pages"] == 2
    assert data["items"] == [reports[1]]

from unittest import mock

import pytest

from tests.unit_tests.conftest import (
    api_delete,
    api_post,
    api_put,
)

# --- Admin location tests ---


@mock.patch("goodmap.admin_api.uuid.uuid4")
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


@mock.patch("goodmap.admin_api.uuid.uuid4")
def test_admin_post_location_without_remark_excludes_remark_from_response(mock_uuid4, test_app):
    from uuid import UUID

    mock_uuid4.return_value = UUID("00000000-0000-0000-0000-000000000002")
    data = {
        "uuid": None,
        "name": "NoRemarkLocation",
        "type_of_place": "Type",
        "test_category": ["cat"],
        "position": [10.0, 20.0],
    }
    response = api_post(test_app, "/api/admin/locations", data)
    assert response.status_code == 200
    resp_json = response.json
    assert "remark" not in resp_json, "remark should not be in response when not provided"


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


def test_admin_put_location_not_found(test_app):
    """Test LocationNotFoundError handler when updating non-existent location."""
    from goodmap.exceptions import LocationNotFoundError

    db = test_app.application.db
    valid_location = {
        "name": "Test",
        "position": [50, 50],
        "test_category": ["test"],
        "type_of_place": "test",
    }
    with mock.patch.object(db, "update_location", side_effect=LocationNotFoundError("nonexistent")):
        response = api_put(test_app, "/api/admin/locations/nonexistent", valid_location)
        assert response.status_code == 404
        assert "not found" in response.json["message"].lower()


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

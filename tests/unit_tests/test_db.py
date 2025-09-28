import json
from typing import Any, cast
from unittest import mock

import pytest
from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_db import Json
from platzky.db.json_file_db import JsonFile
from platzky.db.mongodb_db import MongoDB

from goodmap.data_models.location import LocationBase, create_location_model
from goodmap.db import (
    add_location,
    add_report,
    add_suggestion,
    delete_location,
    delete_report,
    delete_suggestion,
    extend_db_with_goodmap_queries,
    get_data,
    get_location_from_raw_data,
    get_location_obligatory_fields,
    google_json_db_get_categories,
    google_json_db_get_category_data,
    google_json_db_get_data,
    google_json_db_get_location_obligatory_fields,
    json_db_add_location,
    json_db_add_report,
    json_db_add_suggestion,
    json_db_delete_location,
    json_db_delete_report,
    json_db_delete_suggestion,
    json_db_get_categories,
    json_db_get_category_data,
    json_db_get_data,
    json_db_get_location_obligatory_fields,
    json_db_get_report,
    json_db_get_reports,
    json_db_get_suggestion,
    json_db_get_suggestions,
    json_db_update_location,
    json_db_update_report,
    json_db_update_suggestion,
    json_file_atomic_dump,
    json_file_db_add_location,
    json_file_db_add_report,
    json_file_db_add_suggestion,
    json_file_db_delete_location,
    json_file_db_delete_report,
    json_file_db_delete_suggestion,
    json_file_db_get_categories,
    json_file_db_get_category_data,
    json_file_db_get_data,
    json_file_db_get_location_obligatory_fields,
    json_file_db_get_report,
    json_file_db_get_reports,
    json_file_db_get_suggestion,
    json_file_db_get_suggestions,
    json_file_db_update_location,
    json_file_db_update_report,
    json_file_db_update_suggestion,
    mongodb_db_add_location,
    mongodb_db_add_report,
    mongodb_db_add_suggestion,
    mongodb_db_delete_location,
    mongodb_db_delete_report,
    mongodb_db_delete_suggestion,
    mongodb_db_get_categories,
    mongodb_db_get_category_data,
    mongodb_db_get_data,
    mongodb_db_get_location,
    mongodb_db_get_location_obligatory_fields,
    mongodb_db_get_locations,
    mongodb_db_get_report,
    mongodb_db_get_reports,
    mongodb_db_get_suggestion,
    mongodb_db_get_suggestions,
    mongodb_db_update_location,
    mongodb_db_update_report,
    mongodb_db_update_suggestion,
    update_location,
    update_report,
    update_suggestion,
)

data = {
    "data": [
        {"position": [50, 50], "uuid": "1", "name": "one", "test-category": "searchable"},
        {"position": [10, 10], "uuid": "2", "name": "two", "test-category": "unsearchable"},
    ],
    "categories": {"test-category": ["searchable", "unsearchable"]},
    "location_obligatory_fields": [["name", "str"]],
    "categories_help": ["Help text for categories"],
    "categories_options_help": {"test-category": ["Help for test category"]},
}
data_json = json.dumps({"map": data})


def initialize_and_assert_db(db, data):
    location_obligatory_fields = get_location_obligatory_fields(db)
    location_model = create_location_model(location_obligatory_fields)
    extend_db_with_goodmap_queries(db, location_model)

    query = {"test-category": "searchable"}

    location = db.get_location("1")
    assert location.position == (50, 50)
    assert location.uuid == "1"

    assert len(db.get_locations(query)) == 2
    assert db.get_data() == data


def test_goodmap_json_db_extended():
    db = Json(data)
    initialize_and_assert_db(db, data)


@mock.patch("builtins.open", mock.mock_open(read_data=data_json))
def test_goodmap_json_db_file_extended():
    db = JsonFile("/fake/path/file.json")
    initialize_and_assert_db(db, data)


@mock.patch("platzky.db.google_json_db.Client")
def test_goodmap_google_json_db_extended(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    initialize_and_assert_db(db, data)


@mock.patch("goodmap.db.json.dump")
@mock.patch("goodmap.db.tempfile.NamedTemporaryFile")
@mock.patch("goodmap.db.os.fsync")
@mock.patch("goodmap.db.os.replace")
def test_json_file_atomic_dump(mock_replace, mock_fsync, mock_tempfile, mock_json_dump):
    file_path = "atomic.json"
    payload = {"key": "value", "list": [1, 2, 3]}
    json_file_atomic_dump(payload, file_path)
    mock_tempfile.assert_called_once_with("w", dir="", delete=False)
    mock_json_dump.assert_called_once_with(payload, mock_tempfile().__enter__())
    mock_tempfile().__enter__().flush.assert_called_once()
    mock_fsync.assert_called_once_with(mock_tempfile().__enter__().fileno())
    mock_replace.assert_called_once_with(mock_tempfile().__enter__().name, file_path)


def test_json_db_get_location_obligatory_fields():
    db = Json(data={"location_obligatory_fields": ["field"]})
    assert json_db_get_location_obligatory_fields(db) == ["field"]


@mock.patch(
    "builtins.open",
    mock.mock_open(read_data=json.dumps({"map": {"location_obligatory_fields": [1, 2, 3]}})),
)
def test_json_file_db_get_location_obligatory_fields():
    db = JsonFile("/fake/db.json")
    assert json_file_db_get_location_obligatory_fields(db) == [1, 2, 3]


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_location_obligatory_fields(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {"location_obligatory_fields": [9]}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert google_json_db_get_location_obligatory_fields(db) == [9]


def test_get_data_dispatch_json_db():
    db = Json({})
    assert get_data(db) is json_db_get_data


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {}})))
def test_get_data_dispatch_json_file_db():
    db = JsonFile("/fake/path/data.json")
    assert get_data(db) is json_file_db_get_data


@mock.patch("platzky.db.google_json_db.Client")
def test_get_data_dispatch_google_json_db(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert get_data(db) is google_json_db_get_data


def test_json_db_get_data_returns_data():
    db = Json({"foo": "bar"})
    assert json_db_get_data(db) == {"foo": "bar"}


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"a": 1}})))
def test_json_file_db_get_data_reads_file():
    db = JsonFile("/fake/path/data.json")
    assert json_file_db_get_data(db) == {"a": 1}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_data(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {"x": 1}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert google_json_db_get_data(db) == {"x": 1}


def test_get_location_from_raw_data_found():
    raw = {"data": [{"uuid": "X", "position": [0, 0]}]}
    Location = create_location_model([])
    location: Any = get_location_from_raw_data(raw, "X", Location)
    assert location is not None
    assert location.uuid == "X"
    assert location.position == (0, 0)


def test_get_location_from_raw_data_not_found():
    raw = {"data": [{"uuid": "X", "position": [0, 0]}]}
    Location = create_location_model([])
    assert get_location_from_raw_data(raw, "Y", Location) is None


def test_json_db_add_location():
    Location = create_location_model([])
    db = Json({"data": []})
    location = {"uuid": "1", "position": [1, 2]}
    json_db_add_location(db, location, Location)
    assert len(db.data["data"]) == 1
    assert tuple(db.data["data"][0]["position"]) == (1, 2)


def test_json_db_add_duplicate_location():
    Location = create_location_model([])
    db = Json({"data": []})
    location = {"uuid": "1", "position": [1, 2]}
    json_db_add_location(db, location, Location)
    with pytest.raises(ValueError):
        json_db_add_location(db, location, Location)


def test_json_db_update_location():
    Location = create_location_model([])
    db = Json({"data": [{"uuid": "1", "position": [1, 2]}]})
    location_update = {"uuid": "1", "position": [3, 4]}
    json_db_update_location(db, "1", location_update, Location)
    assert tuple(db.data["data"][0]["position"]) == (3, 4)


def test_json_db_update_location_not_found():
    Location = create_location_model([])
    db = Json({"data": []})
    location_update = {"uuid": "1", "position": [3, 4]}
    with pytest.raises(ValueError):
        json_db_update_location(db, "1", location_update, Location)


def test_json_db_delete_location():
    db = Json({"data": [{"uuid": "1", "position": [1, 2]}]})
    json_db_delete_location(db, "1")
    assert db.data["data"] == []


def test_json_db_delete_location_not_found():
    db = Json({"data": []})
    with pytest.raises(ValueError):
        json_db_delete_location(db, "1")


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"data": []}})))
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_add_location(mock_atomic_dump):
    Location = create_location_model([])
    file_path = "locs.json"
    db = JsonFile(file_path)
    location_raw = {"uuid": "a", "position": [5, 6]}
    json_file_db_add_location(db, location_raw, Location)
    location = Location.model_validate(location_raw).model_dump()
    mock_atomic_dump.assert_called_once_with({"map": {"data": [location]}}, file_path)


@mock.patch(
    "builtins.open",
    mock.mock_open(read_data=json.dumps({"map": {"data": [{"uuid": "a", "position": [5, 6]}]}})),
)
def test_json_file_db_add_duplicate_location():
    Location = create_location_model([])
    file_path = "locs.json"
    db = JsonFile(file_path)
    location = {"uuid": "a", "position": [5, 6]}
    with pytest.raises(ValueError):
        json_file_db_add_location(db, location, Location)


@mock.patch(
    "builtins.open",
    mock.mock_open(read_data=json.dumps({"map": {"data": [{"uuid": "a", "position": [5, 6]}]}})),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_update_location(mock_atomic_dump):
    Location = create_location_model([])
    file_path = "locs.json"
    db = JsonFile(file_path)
    location_update_raw = {"uuid": "a", "position": [7, 8]}
    json_file_db_update_location(db, "a", location_update_raw, Location)
    location_update = Location.model_validate(location_update_raw).model_dump()
    mock_atomic_dump.assert_called_once_with({"map": {"data": [location_update]}}, file_path)


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"data": []}})))
def test_json_file_db_update_location_not_found():
    Location = create_location_model([])
    file_path = "locs.json"
    db = JsonFile(file_path)
    location_update_raw = {"uuid": "a", "position": [7, 8]}
    with pytest.raises(ValueError):
        json_file_db_update_location(db, "a", location_update_raw, Location)


@mock.patch(
    "builtins.open",
    mock.mock_open(read_data=json.dumps({"map": {"data": [{"uuid": "a", "position": [5, 6]}]}})),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_delete_location(mock_atomic_dump):
    file_path = "locs.json"
    db = JsonFile(file_path)
    json_file_db_delete_location(db, "a")
    mock_atomic_dump.assert_called_once_with({"map": {"data": []}}, file_path)


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"data": []}})))
def test_json_file_db_delete_location_not_found():
    file_path = "locs.json"
    db = JsonFile(file_path)
    with pytest.raises(ValueError):
        json_file_db_delete_location(db, "a")


def test_json_db_add_suggestion():
    db = Json({})
    suggestion = {"uuid": "s1", "foo": "bar"}
    json_db_add_suggestion(db, suggestion)
    assert len(db.data["suggestions"]) == 1
    assert db.data["suggestions"][0]["status"] == "pending"


def test_json_db_add_duplicate_suggestion():
    db = Json({})
    suggestion = {"uuid": "s1"}
    json_db_add_suggestion(db, suggestion)
    with pytest.raises(ValueError):
        json_db_add_suggestion(db, suggestion)


def test_json_db_get_suggestions_filters():
    suggestions = [
        {"uuid": "s1", "status": "pending"},
        {"uuid": "s2", "status": "done"},
    ]
    db = Json({"suggestions": suggestions})
    all_suggestions = json_db_get_suggestions(db, {})
    assert len(all_suggestions) == 2
    pending = json_db_get_suggestions(db, {"status": ["pending"]})
    assert len(pending) == 1 and pending[0]["uuid"] == "s1"


def test_json_db_get_suggestion_by_uuid():
    db = Json({"suggestions": [{"uuid": "s1", "status": "pending"}]})
    suggestion = json_db_get_suggestion(db, "s1")
    assert suggestion is not None and suggestion["uuid"] == "s1"
    assert json_db_get_suggestion(db, "x") is None


def test_json_db_update_suggestion():
    db = Json({"suggestions": [{"uuid": "s1", "status": "pending"}]})
    json_db_update_suggestion(db, "s1", "done")
    assert db.data["suggestions"][0]["status"] == "done"


def test_json_db_update_suggestion_not_found():
    db = Json({"suggestions": []})
    with pytest.raises(ValueError):
        json_db_update_suggestion(db, "x", "new")


def test_json_db_update_suggestion_multiple():
    # First element should remain unchanged, second updated
    suggestions = [
        {"uuid": "a", "status": "pending"},
        {"uuid": "b", "status": "pending"},
    ]
    db = Json({"suggestions": [s.copy() for s in suggestions]})
    json_db_update_suggestion(db, "b", "done")
    assert db.data["suggestions"][0]["status"] == "pending"
    assert db.data["suggestions"][1]["status"] == "done"


def test_json_db_delete_suggestion():
    db = Json({"suggestions": [{"uuid": "s1"}]})
    json_db_delete_suggestion(db, "s1")
    assert db.data["suggestions"] == []


def test_json_db_delete_suggestion_not_found():
    db = Json({"suggestions": []})
    with pytest.raises(ValueError):
        json_db_delete_suggestion(db, "s1")


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"suggestions": []}})))
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_add_suggestion(mock_atomic_dump):
    file_path = "sug.json"
    db = JsonFile(file_path)
    suggestion_raw = {"uuid": "s1", "foo": "bar"}
    json_file_db_add_suggestion(db, suggestion_raw)
    suggestion = suggestion_raw.copy()
    suggestion["status"] = "pending"
    mock_atomic_dump.assert_called_once_with({"map": {"suggestions": [suggestion]}}, file_path)


@mock.patch(
    "builtins.open",
    mock.mock_open(read_data=json.dumps({"map": {"suggestions": [{"uuid": "s1"}]}})),
)
def test_json_file_db_add_duplicate_suggestion():
    file_path = "sug.json"
    db = JsonFile(file_path)
    suggestion = {"uuid": "s1"}
    with pytest.raises(ValueError):
        json_file_db_add_suggestion(db, suggestion)


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps(
            {
                "map": {
                    "suggestions": [
                        {"uuid": "s1", "status": "pending"},
                        {"uuid": "s2", "status": "done"},
                    ]
                }
            }
        )
    ),
)
def test_json_file_db_get_suggestions_filters():
    file_path = "sug.json"
    db = JsonFile(file_path)
    all_suggestions = json_file_db_get_suggestions(db, {})
    assert len(all_suggestions) == 2
    pending = json_file_db_get_suggestions(db, {"status": ["pending"]})
    assert len(pending) == 1 and pending[0]["uuid"] == "s1"


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps({"map": {"suggestions": [{"uuid": "s1", "status": "pending"}]}})
    ),
)
def test_json_file_db_get_suggestion_by_uuid():
    file_path = "sug.json"
    db = JsonFile(file_path)
    suggestion = json_file_db_get_suggestion(db, "s1")
    assert suggestion is not None and suggestion["uuid"] == "s1"
    assert json_file_db_get_suggestion(db, "x") is None


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps({"map": {"suggestions": [{"uuid": "s1", "status": "pending"}]}})
    ),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_update_suggestion(mock_atomic_dump):
    file_path = "sug.json"
    db = JsonFile(file_path)
    json_file_db_update_suggestion(db, "s1", "done")
    suggestion = {"uuid": "s1", "status": "done"}
    mock_atomic_dump.assert_called_once_with({"map": {"suggestions": [suggestion]}}, file_path)


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"suggestions": []}})))
def test_json_file_db_update_suggestion_not_found():
    file_path = "sug.json"
    db = JsonFile(file_path)
    with pytest.raises(ValueError):
        json_file_db_update_suggestion(db, "x", "new")


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps(
            {
                "map": {
                    "suggestions": [
                        {"uuid": "a", "status": "pending"},
                        {"uuid": "b", "status": "pending"},
                    ]
                }
            }
        )
    ),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_update_suggestion_multiple(mock_atomic_dump):
    file_path = "sug.json"
    db = JsonFile(file_path)
    json_file_db_update_suggestion(db, "b", "done")
    rec1 = {"uuid": "a", "status": "pending"}
    rec2 = {"uuid": "b", "status": "done"}
    expected = {"map": {"suggestions": [rec1, rec2]}}
    mock_atomic_dump.assert_called_once_with(expected, file_path)


@mock.patch(
    "builtins.open",
    mock.mock_open(read_data=json.dumps({"map": {"suggestions": [{"uuid": "s1"}]}})),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_delete_suggestion(mock_atomic_dump):
    file_path = "sug.json"
    db = JsonFile(file_path)
    json_file_db_delete_suggestion(db, "s1")
    mock_atomic_dump.assert_called_once_with({"map": {"suggestions": []}}, file_path)


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"suggestions": []}})))
def test_json_file_db_delete_suggestion_not_found():
    file_path = "sug.json"
    db = JsonFile(file_path)
    with pytest.raises(ValueError):
        json_file_db_delete_suggestion(db, "s1")


def test_json_db_add_report():
    db = Json({})
    report = {"uuid": "r1", "status": "new", "priority": "high"}
    json_db_add_report(db, report)
    assert len(db.data["reports"]) == 1


def test_json_db_add_duplicate_report():
    db = Json({})
    report = {"uuid": "r1"}
    json_db_add_report(db, report)
    with pytest.raises(ValueError):
        json_db_add_report(db, report)


def test_json_db_get_reports_filters():
    db = Json(
        {
            "reports": [
                {"uuid": "r1", "status": "new", "priority": "high"},
                {"uuid": "r2", "status": "done", "priority": "low"},
            ]
        }
    )
    all_reports = json_db_get_reports(db, {})
    assert len(all_reports) == 2
    status_reports = json_db_get_reports(db, {"status": ["new"]})
    assert len(status_reports) == 1 and status_reports[0]["uuid"] == "r1"
    priority_reports = json_db_get_reports(db, {"priority": ["low"]})
    assert len(priority_reports) == 1 and priority_reports[0]["uuid"] == "r2"


def test_json_db_get_report_by_uuid():
    db = Json({"reports": [{"uuid": "r1"}]})
    report = json_db_get_report(db, "r1")
    assert report is not None and report["uuid"] == "r1"
    assert json_db_get_report(db, "x") is None


def test_json_db_update_report_fields():
    db = Json({"reports": [{"uuid": "r1", "status": "new", "priority": "high"}]})
    json_db_update_report(db, "r1", status="done")
    assert db.data["reports"][0]["status"] == "done"
    json_db_update_report(db, "r1", priority="low")
    assert db.data["reports"][0]["priority"] == "low"
    json_db_update_report(db, "r1", status="new", priority="high")
    assert db.data["reports"][0]["status"] == "new"
    assert db.data["reports"][0]["priority"] == "high"


def test_json_db_update_report_not_found():
    db = Json({"reports": []})
    with pytest.raises(ValueError):
        json_db_update_report(db, "x", status="a")


def test_json_db_update_report_multiple():
    # First report unchanged, second updated
    reports = [
        {"uuid": "r1", "status": "pending", "priority": "low"},
        {"uuid": "r2", "status": "pending", "priority": "low"},
    ]
    db = Json({"reports": [r.copy() for r in reports]})
    json_db_update_report(db, "r2", status="resolved", priority=None)
    assert db.data["reports"][0]["status"] == "pending"
    assert db.data["reports"][1]["status"] == "resolved"


def test_json_db_delete_report():
    db = Json({"reports": [{"uuid": "r1"}]})
    json_db_delete_report(db, "r1")
    assert db.data["reports"] == []


def test_json_db_delete_report_not_found():
    db = Json({"reports": []})
    with pytest.raises(ValueError):
        json_db_delete_report(db, "r1")


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"reports": []}})))
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_add_report(mock_atomic_dump):
    file_path = "rep.json"
    db = JsonFile(file_path)
    report = {"uuid": "r1", "status": "new", "priority": "high"}
    json_file_db_add_report(db, report)
    mock_atomic_dump.assert_called_once_with({"map": {"reports": [report]}}, file_path)


@mock.patch(
    "builtins.open", mock.mock_open(read_data=json.dumps({"map": {"reports": [{"uuid": "r1"}]}}))
)
def test_json_file_db_add_duplicate_report():
    file_path = "rep.json"
    db = JsonFile(file_path)
    report = {"uuid": "r1"}
    with pytest.raises(ValueError):
        json_file_db_add_report(db, report)


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps(
            {
                "map": {
                    "reports": [
                        {"uuid": "r1", "status": "new", "priority": "high"},
                        {"uuid": "r2", "status": "done", "priority": "low"},
                    ]
                }
            }
        )
    ),
)
def test_json_file_db_get_reports_filters():
    file_path = "rep.json"
    db = JsonFile(file_path)
    all_reports = json_file_db_get_reports(db, {})
    assert len(all_reports) == 2
    status_reports = json_file_db_get_reports(db, {"status": ["new"]})
    assert len(status_reports) == 1 and status_reports[0]["uuid"] == "r1"
    priority_reports = json_file_db_get_reports(db, {"priority": ["low"]})
    assert len(priority_reports) == 1 and priority_reports[0]["uuid"] == "r2"


@mock.patch(
    "builtins.open", mock.mock_open(read_data=json.dumps({"map": {"reports": [{"uuid": "r1"}]}}))
)
def test_json_file_db_get_report_by_uuid():
    file_path = "rep.json"
    db = JsonFile(file_path)
    report = json_file_db_get_report(db, "r1")
    assert report is not None and report["uuid"] == "r1"
    assert json_file_db_get_report(db, "x") is None


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps(
            {"map": {"reports": [{"uuid": "r1", "status": "new", "priority": "high"}]}}
        )
    ),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_update_report_fields(mock_atomic_dump):
    file_path = "rep.json"
    db = JsonFile(file_path)
    original_report = {"uuid": "r1", "status": "new", "priority": "high"}

    json_file_db_update_report(db, "r1", status="done")
    report = original_report.copy()
    report["status"] = "done"
    mock_atomic_dump.assert_called_with({"map": {"reports": [report]}}, file_path)

    json_file_db_update_report(db, "r1", priority="low")
    report = original_report.copy()
    report["priority"] = "low"
    mock_atomic_dump.assert_called_with({"map": {"reports": [report]}}, file_path)

    json_file_db_update_report(db, "r1", status="done", priority="low")
    report = original_report.copy()
    report["status"] = "done"
    report["priority"] = "low"
    mock_atomic_dump.assert_called_with({"map": {"reports": [report]}}, file_path)


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"reports": []}})))
def test_json_file_db_update_report_not_found():
    file_path = "rep.json"
    db = JsonFile(file_path)
    with pytest.raises(ValueError):
        json_file_db_update_report(db, "x", status="a")


@mock.patch(
    "builtins.open",
    mock.mock_open(
        read_data=json.dumps(
            {
                "map": {
                    "reports": [
                        {"uuid": "r1", "status": "pending", "priority": "low"},
                        {"uuid": "r2", "status": "pending", "priority": "low"},
                    ]
                }
            }
        )
    ),
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_update_report_multiple(mock_atomic_dump):
    file_path = "rep.json"
    db = JsonFile(file_path)
    json_file_db_update_report(db, "r2", priority="critical")
    rec1 = {"uuid": "r1", "status": "pending", "priority": "low"}
    rec2 = {"uuid": "r2", "status": "pending", "priority": "critical"}
    expected = {"map": {"reports": [rec1, rec2]}}
    mock_atomic_dump.assert_called_once_with(expected, file_path)


@mock.patch(
    "builtins.open", mock.mock_open(read_data=json.dumps({"map": {"reports": [{"uuid": "r1"}]}}))
)
@mock.patch("goodmap.db.json_file_atomic_dump")
def test_json_file_db_delete_report(mock_atomic_dump):
    file_path = "rep.json"
    db = JsonFile(file_path)
    json_file_db_delete_report(db, "r1")
    mock_atomic_dump.assert_called_once_with({"map": {"reports": []}}, file_path)


@mock.patch("builtins.open", mock.mock_open(read_data=json.dumps({"map": {"reports": []}})))
def test_json_file_db_delete_report_not_found():
    file_path = "rep.json"
    db = JsonFile(file_path)
    with pytest.raises(ValueError):
        json_file_db_delete_report(db, "r1")


def test_dispatch_add_update_delete_location():
    db = Json({"data": []})
    Location = create_location_model([])

    loc = {"uuid": "u1", "position": [10, 20]}
    add_location(db, loc, Location)
    assert db.data["data"][0]["uuid"] == "u1"

    updated = {"uuid": "u1", "position": [30, 40]}
    update_location(db, "u1", updated, Location)
    assert tuple(db.data["data"][0]["position"]) == (30, 40)

    delete_location(db, "u1")
    assert db.data["data"] == []


def test_dispatch_add_update_delete_suggestion():
    db = Json({"suggestions": []})

    sugg = {"uuid": "s1", "foo": "bar"}
    add_suggestion(db, sugg)
    assert db.data["suggestions"][0]["status"] == "pending"

    update_suggestion(db, "s1", "done")
    assert db.data["suggestions"][0]["status"] == "done"

    delete_suggestion(db, "s1")
    assert db.data["suggestions"] == []


def test_dispatch_add_update_delete_report():
    db = Json({"reports": []})

    rep = {"uuid": "r1", "status": "new", "priority": "high"}
    add_report(db, rep)
    assert db.data["reports"][0]["uuid"] == "r1"

    update_report(db, "r1", status="resolved", priority="low")
    assert db.data["reports"][0]["status"] == "resolved"
    assert db.data["reports"][0]["priority"] == "low"

    delete_report(db, "r1")
    assert db.data["reports"] == []


# MongoDB tests
@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location_obligatory_fields(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "location_obligatory_fields": ["name", "position"],
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location_obligatory_fields(db)
    assert result == ["name", "position"]
    mock_db.config.find_one.assert_called_once_with({"_id": "map_config"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location_obligatory_fields_empty(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location_obligatory_fields(db)
    assert result == []


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_data(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "location_obligatory_fields": ["name"],
        "visible_data": {"key": "value"},
        "meta_data": {"meta": "info"},
    }
    mock_db.locations.find.return_value = [{"uuid": "1", "position": [50, 50], "name": "one"}]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_data(db)

    expected = {
        "data": [{"uuid": "1", "position": [50, 50], "name": "one"}],
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "location_obligatory_fields": ["name"],
        "visible_data": {"key": "value"},
        "meta_data": {"meta": "info"},
    }
    assert result == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_data_no_config(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_data(db)

    expected = {
        "data": [],
        "categories": {},
        "location_obligatory_fields": [],
        "visible_data": {},
        "meta_data": {},
    }
    assert result == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.locations.find_one.return_value = {"uuid": "1", "position": [50, 50], "name": "one"}

    Location = create_location_model([])
    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location(db, "1", Location)

    assert result is not None
    result = cast(LocationBase, result)
    assert result.uuid == "1"
    assert result.position == (50, 50)
    mock_db.locations.find_one.assert_called_once_with({"uuid": "1"}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.locations.find_one.return_value = None

    Location = create_location_model([])
    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location(db, "nonexistent", Location)

    assert result is None


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_location(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.locations.find_one.return_value = None  # No existing location

    Location = create_location_model([])
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": "new1", "position": [10, 20]}

    mongodb_db_add_location(db, location_data, Location)

    mock_db.locations.find_one.assert_called_once_with({"uuid": "new1"})
    mock_db.locations.insert_one.assert_called_once()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_duplicate_location(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.locations.find_one.return_value = {"uuid": "existing"}

    Location = create_location_model([])
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": "existing", "position": [10, 20]}

    with pytest.raises(ValueError, match="Location with uuid existing already exists"):
        mongodb_db_add_location(db, location_data, Location)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_location(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.matched_count = 1
    mock_db.locations.update_one.return_value = mock_result

    Location = create_location_model([])
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": "1", "position": [30, 40]}

    mongodb_db_update_location(db, "1", location_data, Location)

    mock_db.locations.update_one.assert_called_once()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_location_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.matched_count = 0
    mock_db.locations.update_one.return_value = mock_result

    Location = create_location_model([])
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": "nonexistent", "position": [30, 40]}

    with pytest.raises(ValueError, match="Location with uuid nonexistent not found"):
        mongodb_db_update_location(db, "nonexistent", location_data, Location)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_location(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.deleted_count = 1
    mock_db.locations.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_delete_location(db, "1")

    mock_db.locations.delete_one.assert_called_once_with({"uuid": "1"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_location_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.deleted_count = 0
    mock_db.locations.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Location with uuid nonexistent not found"):
        mongodb_db_delete_location(db, "nonexistent")


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_suggestion(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.suggestions.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    suggestion_data = {"uuid": "s1", "content": "test suggestion"}

    mongodb_db_add_suggestion(db, suggestion_data)

    mock_db.suggestions.find_one.assert_called_once_with({"uuid": "s1"})
    mock_db.suggestions.insert_one.assert_called_once()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_duplicate_suggestion(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.suggestions.find_one.return_value = {"uuid": "s1"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    suggestion_data = {"uuid": "s1", "content": "test"}

    with pytest.raises(ValueError, match="Suggestion with uuid s1 already exists"):
        mongodb_db_add_suggestion(db, suggestion_data)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_suggestions(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.suggestions.find.return_value = [{"uuid": "s1", "status": "pending"}]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_suggestions(db, {"status": ["pending"]})

    expected_query = {"status": {"$in": ["pending"]}}
    mock_db.suggestions.find.assert_called_once_with(expected_query, {"_id": 0})
    assert result == [{"uuid": "s1", "status": "pending"}]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_suggestions_no_status(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.suggestions.find.return_value = [
        {"uuid": "s1", "status": "pending"},
        {"uuid": "s2", "status": "done"},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_suggestions(db, {})

    mock_db.suggestions.find.assert_called_once_with({}, {"_id": 0})
    assert result == [{"uuid": "s1", "status": "pending"}, {"uuid": "s2", "status": "done"}]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_suggestion(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.suggestions.find_one.return_value = {"uuid": "s1", "content": "test"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_suggestion(db, "s1")

    assert result == {"uuid": "s1", "content": "test"}
    mock_db.suggestions.find_one.assert_called_once_with({"uuid": "s1"}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_suggestion(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.matched_count = 1
    mock_db.suggestions.update_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_update_suggestion(db, "s1", "approved")

    mock_db.suggestions.update_one.assert_called_once_with(
        {"uuid": "s1"}, {"$set": {"status": "approved"}}
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_suggestion_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.matched_count = 0
    mock_db.suggestions.update_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Suggestion with uuid nonexistent not found"):
        mongodb_db_update_suggestion(db, "nonexistent", "approved")


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_suggestion(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.deleted_count = 1
    mock_db.suggestions.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_delete_suggestion(db, "s1")

    mock_db.suggestions.delete_one.assert_called_once_with({"uuid": "s1"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_suggestion_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.deleted_count = 0
    mock_db.suggestions.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Suggestion with uuid nonexistent not found"):
        mongodb_db_delete_suggestion(db, "nonexistent")


def test_json_db_get_categories():
    db = Json(data)
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = json_db_get_categories(db)
    assert list(categories) == ["test-category"]


def test_json_file_db_get_categories(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = json_file_db_get_categories(db)
    assert list(categories) == ["test-category"]


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_categories(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = google_json_db_get_categories(db)
    assert list(categories) == ["test-category"]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_categories(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = mongodb_db_get_categories(db)
    assert categories == ["test-category"]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_categories_no_config(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = mongodb_db_get_categories(db)
    assert categories == []


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_categories_no_categories_field(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = {"_id": "map_config"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = mongodb_db_get_categories(db)
    assert categories == []


def test_get_categories():
    db = Json(data)
    extend_db_with_goodmap_queries(db, LocationBase)
    categories = json_db_get_categories(db)
    assert list(categories) == ["test-category"]


def test_json_db_get_category_data():
    db = Json(data)
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = json_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


def test_json_db_get_category_data_specific_category():
    db = Json(data)
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = json_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


def test_json_file_db_get_category_data(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = json_file_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


def test_json_file_db_get_category_data_specific_category(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = json_file_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_category_data(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = google_json_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_category_data_specific_category(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = google_json_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_category_data(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = mongodb_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_category_data_specific_category(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = mongodb_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_category_data_no_config(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = mongodb_db_get_category_data(db)
    expected = {"categories": {}, "categories_help": [], "categories_options_help": {}}
    assert category_data == expected


def test_get_category_data():
    db = Json(data)
    extend_db_with_goodmap_queries(db, LocationBase)
    category_data = json_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.locations.find.return_value = [
        {"uuid": "1", "position": [50, 50]},
        {"uuid": "2", "position": [10, 10]},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)

    query = {"test-category": ["searchable"]}
    locations = list(mongodb_db_get_locations(db, query, LocationBase))

    assert len(locations) == 2
    assert locations[0].uuid == "1"
    assert locations[0].position == (50, 50)
    assert locations[1].uuid == "2"
    assert locations[1].position == (10, 10)

    mock_db.locations.find.assert_called_once_with(
        {"test-category": {"$in": ["searchable"]}}, {"_id": 0, "uuid": 1, "position": 1}
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations_empty_query(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.locations.find.return_value = []

    db = MongoDB("mongodb://localhost:27017", "test_db")
    extend_db_with_goodmap_queries(db, LocationBase)

    query = {"test-category": []}
    locations = list(mongodb_db_get_locations(db, query, LocationBase))

    assert len(locations) == 0
    mock_db.locations.find.assert_called_once_with({}, {"_id": 0, "uuid": 1, "position": 1})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_report(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.reports.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    report_data = {"uuid": "r1", "content": "test report"}
    mongodb_db_add_report(db, report_data)

    mock_db.reports.find_one.assert_called_once_with({"uuid": "r1"})
    mock_db.reports.insert_one.assert_called_once_with(report_data)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_report_already_exists(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.reports.find_one.return_value = {"uuid": "r1", "content": "existing"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    report_data = {"uuid": "r1", "content": "test report"}

    with pytest.raises(ValueError, match="Report with uuid r1 already exists"):
        mongodb_db_add_report(db, report_data)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_reports(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.reports.find.return_value = [
        {"uuid": "r1", "status": "open", "priority": "high"},
        {"uuid": "r2", "status": "closed", "priority": "low"},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query_params = {"status": ["open"], "priority": ["high"]}
    reports = mongodb_db_get_reports(db, query_params)

    assert len(reports) == 2
    mock_db.reports.find.assert_called_once_with(
        {"status": {"$in": ["open"]}, "priority": {"$in": ["high"]}}, {"_id": 0}
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_reports_empty_query(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.reports.find.return_value = []

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query_params = {}
    reports = mongodb_db_get_reports(db, query_params)

    assert len(reports) == 0
    mock_db.reports.find.assert_called_once_with({}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_report(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_db.reports.find_one.return_value = {"uuid": "r1", "content": "test"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_report(db, "r1")

    assert result == {"uuid": "r1", "content": "test"}
    mock_db.reports.find_one.assert_called_once_with({"uuid": "r1"}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_report(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.matched_count = 1
    mock_db.reports.update_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_update_report(db, "r1", status="closed", priority="high")

    mock_db.reports.update_one.assert_called_once_with(
        {"uuid": "r1"}, {"$set": {"status": "closed", "priority": "high"}}
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_report_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.matched_count = 0
    mock_db.reports.update_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Report with uuid nonexistent not found"):
        mongodb_db_update_report(db, "nonexistent", status="closed")


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_report_no_updates(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_update_report(db, "r1")

    mock_db.reports.update_one.assert_not_called()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_report(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.deleted_count = 1
    mock_db.reports.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_delete_report(db, "r1")

    mock_db.reports.delete_one.assert_called_once_with({"uuid": "r1"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_report_not_found(mock_client):
    mock_db = mock.Mock()
    mock_client.return_value.__getitem__.return_value = mock_db
    mock_result = mock.Mock()
    mock_result.deleted_count = 0
    mock_db.reports.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Report with uuid nonexistent not found"):
        mongodb_db_delete_report(db, "nonexistent")



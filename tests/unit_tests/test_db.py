import json
from typing import Any
from unittest import mock

import pytest
from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_db import Json
from platzky.db.json_file_db import JsonFile

from goodmap.data_models.location import create_location_model
from goodmap.db import (
    extend_db_with_goodmap_queries,
    get_data,
    get_location_from_raw_data,
    get_location_obligatory_fields,
    google_json_db_get_data,
    google_json_db_get_location_obligatory_fields,
    json_db_add_location,
    json_db_add_report,
    json_db_add_suggestion,
    json_db_delete_location,
    json_db_delete_report,
    json_db_delete_suggestion,
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
    json_file_db_get_data,
    json_file_db_get_location_obligatory_fields,
    json_file_db_get_report,
    json_file_db_get_reports,
    json_file_db_get_suggestion,
    json_file_db_get_suggestions,
    json_file_db_update_location,
    json_file_db_update_report,
    json_file_db_update_suggestion,
)

data = {
    "data": [
        {"position": [50, 50], "uuid": "1", "name": "one", "test-category": "searchable"},
        {"position": [10, 10], "uuid": "2", "name": "two", "test-category": "unsearchable"},
    ],
    "categories": {"test-category": ["searchable", "unsearchable"]},
    "location_obligatory_fields": [["name", "str"]],
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


def test_json_file_atomic_dump(tmp_path):
    file_path = tmp_path / "atomic.json"
    payload = {"key": "value", "list": [1, 2, 3]}
    json_file_atomic_dump(payload, file_path)
    with open(file_path, "r") as f:
        loaded = json.load(f)
    assert loaded == payload


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


def test_json_db_delete_location():
    db = Json({"data": [{"uuid": "1", "position": [1, 2]}]})
    json_db_delete_location(db, "1")
    assert db.data["data"] == []


def test_json_db_delete_location_not_found():
    db = Json({"data": []})
    with pytest.raises(ValueError):
        json_db_delete_location(db, "1")


def test_json_file_db_add_location(tmp_path):
    Location = create_location_model([])
    file_path = tmp_path / "locs.json"
    initial = {"map": {"data": []}}
    file_path.write_text(json.dumps(initial))
    db = JsonFile(str(file_path))
    location = {"uuid": "a", "position": [5, 6]}
    json_file_db_add_location(db, location, Location)
    content = json.loads(file_path.read_text())
    assert len(content["map"]["data"]) == 1
    assert tuple(content["map"]["data"][0]["position"]) == (5, 6)


def test_json_file_db_add_duplicate_location(tmp_path):
    Location = create_location_model([])
    file_path = tmp_path / "locs.json"
    initial = {"map": {"data": []}}
    file_path.write_text(json.dumps(initial))
    db = JsonFile(str(file_path))
    location = {"uuid": "a", "position": [5, 6]}
    json_file_db_add_location(db, location, Location)
    with pytest.raises(ValueError):
        json_file_db_add_location(db, location, Location)


def test_json_file_db_update_location(tmp_path):
    Location = create_location_model([])
    file_path = tmp_path / "locs.json"
    data = {"map": {"data": [{"uuid": "a", "position": [5, 6]}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    location_update = {"uuid": "a", "position": [7, 8]}
    json_file_db_update_location(db, "a", location_update, Location)
    content = json.loads(file_path.read_text())
    assert tuple(content["map"]["data"][0]["position"]) == (7, 8)


def test_json_file_db_delete_location(tmp_path):
    file_path = tmp_path / "locs.json"
    data = {"map": {"data": [{"uuid": "a", "position": [5, 6]}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    json_file_db_delete_location(db, "a")
    content = json.loads(file_path.read_text())
    assert content["map"]["data"] == []


def test_json_file_db_delete_location_not_found(tmp_path):
    file_path = tmp_path / "locs.json"
    data = {"map": {"data": []}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
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


def test_json_db_delete_suggestion():
    db = Json({"suggestions": [{"uuid": "s1"}]})
    json_db_delete_suggestion(db, "s1")
    assert db.data["suggestions"] == []


def test_json_db_delete_suggestion_not_found():
    db = Json({"suggestions": []})
    with pytest.raises(ValueError):
        json_db_delete_suggestion(db, "s1")


def test_json_file_db_add_suggestion(tmp_path):
    file_path = tmp_path / "sug.json"
    initial = {"map": {"suggestions": []}}
    file_path.write_text(json.dumps(initial))
    db = JsonFile(str(file_path))
    suggestion = {"uuid": "s1", "foo": "bar"}
    json_file_db_add_suggestion(db, suggestion)
    content = json.loads(file_path.read_text())
    assert len(content["map"]["suggestions"]) == 1
    assert content["map"]["suggestions"][0]["status"] == "pending"


def test_json_file_db_add_duplicate_suggestion(tmp_path):
    file_path = tmp_path / "sug.json"
    initial = {"map": {"suggestions": []}}
    file_path.write_text(json.dumps(initial))
    db = JsonFile(str(file_path))
    suggestion = {"uuid": "s1"}
    json_file_db_add_suggestion(db, suggestion)
    with pytest.raises(ValueError):
        json_file_db_add_suggestion(db, suggestion)


def test_json_file_db_get_suggestions_filters(tmp_path):
    file_path = tmp_path / "sug.json"
    suggestions = [
        {"uuid": "s1", "status": "pending"},
        {"uuid": "s2", "status": "done"},
    ]
    data = {"map": {"suggestions": suggestions}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    all_suggestions = json_file_db_get_suggestions(db, {})
    assert len(all_suggestions) == 2
    pending = json_file_db_get_suggestions(db, {"status": ["pending"]})
    assert len(pending) == 1 and pending[0]["uuid"] == "s1"


def test_json_file_db_get_suggestion_by_uuid(tmp_path):
    file_path = tmp_path / "sug.json"
    data = {"map": {"suggestions": [{"uuid": "s1", "status": "pending"}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    suggestion = json_file_db_get_suggestion(db, "s1")
    assert suggestion is not None and suggestion["uuid"] == "s1"
    assert json_file_db_get_suggestion(db, "x") is None


def test_json_file_db_update_suggestion(tmp_path):
    file_path = tmp_path / "sug.json"
    data = {"map": {"suggestions": [{"uuid": "s1", "status": "pending"}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    json_file_db_update_suggestion(db, "s1", "done")
    content = json.loads(file_path.read_text())
    assert content["map"]["suggestions"][0]["status"] == "done"


def test_json_file_db_update_suggestion_not_found(tmp_path):
    file_path = tmp_path / "sug.json"
    data = {"map": {"suggestions": []}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    with pytest.raises(ValueError):
        json_file_db_update_suggestion(db, "x", "new")


def test_json_file_db_delete_suggestion(tmp_path):
    file_path = tmp_path / "sug.json"
    data = {"map": {"suggestions": [{"uuid": "s1"}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    json_file_db_delete_suggestion(db, "s1")
    content = json.loads(file_path.read_text())
    assert content["map"]["suggestions"] == []


def test_json_file_db_delete_suggestion_not_found(tmp_path):
    file_path = tmp_path / "sug.json"
    data = {"map": {"suggestions": []}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
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


def test_json_db_delete_report():
    db = Json({"reports": [{"uuid": "r1"}]})
    json_db_delete_report(db, "r1")
    assert db.data["reports"] == []


def test_json_db_delete_report_not_found():
    db = Json({"reports": []})
    with pytest.raises(ValueError):
        json_db_delete_report(db, "r1")


def test_json_file_db_add_report(tmp_path):
    file_path = tmp_path / "rep.json"
    initial = {"map": {"reports": []}}
    file_path.write_text(json.dumps(initial))
    db = JsonFile(str(file_path))
    report = {"uuid": "r1", "status": "new", "priority": "high"}
    json_file_db_add_report(db, report)
    content = json.loads(file_path.read_text())
    assert len(content["map"]["reports"]) == 1


def test_json_file_db_add_duplicate_report(tmp_path):
    file_path = tmp_path / "rep.json"
    initial = {"map": {"reports": []}}
    file_path.write_text(json.dumps(initial))
    db = JsonFile(str(file_path))
    report = {"uuid": "r1"}
    json_file_db_add_report(db, report)
    with pytest.raises(ValueError):
        json_file_db_add_report(db, report)


def test_json_file_db_get_reports_filters(tmp_path):
    file_path = tmp_path / "rep.json"
    data = {
        "map": {
            "reports": [
                {"uuid": "r1", "status": "new", "priority": "high"},
                {"uuid": "r2", "status": "done", "priority": "low"},
            ]
        }
    }
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    all_reports = json_file_db_get_reports(db, {})
    assert len(all_reports) == 2
    status_reports = json_file_db_get_reports(db, {"status": ["new"]})
    assert len(status_reports) == 1 and status_reports[0]["uuid"] == "r1"
    priority_reports = json_file_db_get_reports(db, {"priority": ["low"]})
    assert len(priority_reports) == 1 and priority_reports[0]["uuid"] == "r2"


def test_json_file_db_get_report_by_uuid(tmp_path):
    file_path = tmp_path / "rep.json"
    data = {"map": {"reports": [{"uuid": "r1"}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    report = json_file_db_get_report(db, "r1")
    assert report is not None and report["uuid"] == "r1"
    assert json_file_db_get_report(db, "x") is None


def test_json_file_db_update_report_fields(tmp_path):
    file_path = tmp_path / "rep.json"
    data = {"map": {"reports": [{"uuid": "r1", "status": "new", "priority": "high"}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    json_file_db_update_report(db, "r1", status="done")
    content = json.loads(file_path.read_text())
    assert content["map"]["reports"][0]["status"] == "done"
    json_file_db_update_report(db, "r1", priority="low")
    content = json.loads(file_path.read_text())
    assert content["map"]["reports"][0]["priority"] == "low"
    json_file_db_update_report(db, "r1", status="new", priority="high")
    content = json.loads(file_path.read_text())
    assert content["map"]["reports"][0]["status"] == "new"
    assert content["map"]["reports"][0]["priority"] == "high"


def test_json_file_db_update_report_not_found(tmp_path):
    file_path = tmp_path / "rep.json"
    data = {"map": {"reports": []}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    with pytest.raises(ValueError):
        json_file_db_update_report(db, "x", status="a")


def test_json_file_db_delete_report(tmp_path):
    file_path = tmp_path / "rep.json"
    data = {"map": {"reports": [{"uuid": "r1"}]}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    json_file_db_delete_report(db, "r1")
    content = json.loads(file_path.read_text())
    assert content["map"]["reports"] == []


def test_json_file_db_delete_report_not_found(tmp_path):
    file_path = tmp_path / "rep.json"
    data = {"map": {"reports": []}}
    file_path.write_text(json.dumps(data))
    db = JsonFile(str(file_path))
    with pytest.raises(ValueError):
        json_file_db_delete_report(db, "r1")

# pyright: reportArgumentType=false, reportCallIssue=false
import json
from typing import Any, cast
from unittest import mock

import pytest
from platzky.db.github_json_db import GithubJsonDb
from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_db import Json, MemoryStore
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
    get_data,
    get_location_from_raw_data,
    get_location_obligatory_fields,
    goodmap_queries,
    google_json_db_get_categories,
    google_json_db_get_category_data,
    google_json_db_get_data,
    google_json_db_get_initial_view,
    google_json_db_get_location_obligatory_fields,
    google_json_db_get_locations_paginated,
    google_json_db_get_marker_styles,
    google_json_db_get_meta_data,
    google_json_db_get_visible_data,
    json_db_add_location,
    json_db_add_report,
    json_db_add_suggestion,
    json_db_delete_location,
    json_db_delete_report,
    json_db_delete_suggestion,
    json_db_get_categories,
    json_db_get_category_data,
    json_db_get_data,
    json_db_get_initial_view,
    json_db_get_location_obligatory_fields,
    json_db_get_locations,
    json_db_get_report,
    json_db_get_reports,
    json_db_get_suggestion,
    json_db_get_suggestions,
    json_db_update_location,
    json_db_update_report,
    json_db_update_suggestion,
    json_file_db_add_location,
    json_file_db_add_report,
    json_file_db_add_suggestion,
    json_file_db_delete_location,
    json_file_db_delete_report,
    json_file_db_delete_suggestion,
    json_file_db_get_categories,
    json_file_db_get_category_data,
    json_file_db_get_data,
    json_file_db_get_initial_view,
    json_file_db_get_location_obligatory_fields,
    json_file_db_get_locations,
    json_file_db_get_locations_paginated,
    json_file_db_get_marker_styles,
    json_file_db_get_meta_data,
    json_file_db_get_report,
    json_file_db_get_reports,
    json_file_db_get_reports_paginated,
    json_file_db_get_suggestion,
    json_file_db_get_suggestions,
    json_file_db_get_suggestions_paginated,
    json_file_db_get_visible_data,
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
    mongodb_db_get_initial_view,
    mongodb_db_get_location,
    mongodb_db_get_location_obligatory_fields,
    mongodb_db_get_locations,
    mongodb_db_get_locations_paginated,
    mongodb_db_get_marker_styles,
    mongodb_db_get_meta_data,
    mongodb_db_get_report,
    mongodb_db_get_reports,
    mongodb_db_get_reports_paginated,
    mongodb_db_get_suggestion,
    mongodb_db_get_suggestions,
    mongodb_db_get_suggestions_paginated,
    mongodb_db_get_visible_data,
    mongodb_db_update_location,
    mongodb_db_update_report,
    mongodb_db_update_suggestion,
    update_location,
    update_report,
    update_suggestion,
)
from goodmap.exceptions import (
    AlreadyExistsError,
    LocationAlreadyExistsError,
    LocationNotFoundError,
    ReportNotFoundError,
)


def in_memory_json_db(data: dict[str, Any]) -> Json:
    """Json db holding `data` in memory.

    Json takes a JsonStore rather than a raw dict; MemoryStore keeps the passed
    dict as the source of truth, so tests can still assert against `data` itself
    after writes.
    """
    return Json(MemoryStore(data))


def mongo_database(mock_client: mock.Mock) -> mock.Mock:
    """The pymongo database a patched ``MongoClient`` hands to platzky's ``MongoDB``.

    Platzky's own collections are empty, so ``MongoDB`` passes the site config and blog
    validation it runs when it is built; goodmap's collections are left for each test to set.
    """
    database = mock.Mock()
    database.site_config.find_one.return_value = None
    database.localized_content.find.return_value = []
    database.blog_meta.find.return_value = []
    mock_client.return_value.__getitem__.return_value = database
    return database


data = {
    "data": [
        {"position": [50, 50], "uuid": "1", "name": "one", "test-category": "searchable"},
        {"position": [10, 10], "uuid": "2", "name": "two", "test-category": "unsearchable"},
    ],
    "categories": {"test-category": ["searchable", "unsearchable"]},
    "location_obligatory_fields": [["name", "str"]],
    "categories_help": ["Help text for categories"],
    "categories_options_help": {"test-category": ["Help for test category"]},
    "categories_default_checked": {"test-category": ["searchable"]},
}
data_json = json.dumps({"map": data})


def initialize_and_assert_db(db, data):
    location_obligatory_fields = get_location_obligatory_fields(db)
    location_model = create_location_model(location_obligatory_fields, {})
    queries = goodmap_queries(db, location_model)

    # Query values arrive as lists in production (request.args.to_dict(flat=False));
    # a single selected value exactly matches one entry's scalar category field.
    query = {"test-category": ["searchable"]}

    location = queries.get_location("1")
    assert location.position == (50, 50)
    assert location.uuid == "1"

    assert len(queries.get_locations(query)) == 1
    assert queries.get_data() == data


def test_goodmap_json_db_extended():
    db = in_memory_json_db(data)
    initialize_and_assert_db(db, data)


def test_goodmap_json_db_file_extended(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(data_json)
    db = JsonFile(str(db_file))
    initialize_and_assert_db(db, data)


@mock.patch("platzky.db.google_json_db.Client")
def test_goodmap_google_json_db_extended(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    initialize_and_assert_db(db, data)


@mock.patch("platzky.db.github_json_db.Github")
def test_github_json_db_is_not_supported(mock_github):
    mock_github.return_value.get_repo.return_value.get_contents.return_value.decoded_content = b"{}"
    db = GithubJsonDb("token", "owner/repo", "main", "data.json")
    with pytest.raises(NotImplementedError, match="GithubJsonDb"):
        goodmap_queries(db, LocationBase)
    with pytest.raises(NotImplementedError, match="GithubJsonDb"):
        get_location_obligatory_fields(db)


def test_goodmap_queries_leaves_the_database_untouched():
    db = in_memory_json_db(data)
    attributes_before = set(vars(db))
    goodmap_queries(db, LocationBase)
    assert set(vars(db)) == attributes_before


def test_json_db_get_location_obligatory_fields():
    db = in_memory_json_db(data={"location_obligatory_fields": ["field"]})
    assert json_db_get_location_obligatory_fields(db) == ["field"]


def test_json_file_db_get_location_obligatory_fields(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"location_obligatory_fields": [1, 2, 3]}}))
    db = JsonFile(str(db_file))
    assert json_file_db_get_location_obligatory_fields(db) == [1, 2, 3]


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_location_obligatory_fields(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {"location_obligatory_fields": [9]}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert google_json_db_get_location_obligatory_fields(db) == [9]


def test_get_data_dispatch_json_db():
    db = in_memory_json_db({})
    assert get_data(db) is json_db_get_data


def test_get_data_dispatch_json_file_db(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {}}))
    db = JsonFile(str(db_file))
    assert get_data(db) is json_file_db_get_data


@mock.patch("platzky.db.google_json_db.Client")
def test_get_data_dispatch_google_json_db(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert get_data(db) is google_json_db_get_data


def test_json_db_get_data_returns_data():
    db = in_memory_json_db({"foo": "bar"})
    assert json_db_get_data(db) == {"foo": "bar"}


def test_json_file_db_get_data_reads_file(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"a": 1}}))
    db = JsonFile(str(db_file))
    assert json_file_db_get_data(db) == {"a": 1}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_data(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {"x": 1}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert google_json_db_get_data(db) == {"x": 1}


# Test get_visible_data and get_meta_data for json_file_db
def test_json_file_db_get_visible_data(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps({"map": {"visible_data": {"field1": "value1"}, "meta_data": {"meta1": "info1"}}})
    )
    db = JsonFile(str(db_file))
    result = json_file_db_get_visible_data(db)
    assert result == {"field1": "value1"}


def test_json_file_db_get_visible_data_empty(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"visible_data": {}, "meta_data": {"meta1": "info1"}}}))
    db = JsonFile(str(db_file))
    result = json_file_db_get_visible_data(db)
    assert result == {}


def test_json_file_db_get_meta_data(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps({"map": {"visible_data": {"field1": "value1"}, "meta_data": {"meta1": "info1"}}})
    )
    db = JsonFile(str(db_file))
    result = json_file_db_get_meta_data(db)
    assert result == {"meta1": "info1"}


def test_json_file_db_get_meta_data_empty(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"visible_data": {"field1": "value1"}, "meta_data": {}}}))
    db = JsonFile(str(db_file))
    result = json_file_db_get_meta_data(db)
    assert result == {}


def test_json_file_db_get_marker_styles(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "map": {
                    "marker_styles": {
                        "icon_field": "type_of_place",
                        "color_field": "status",
                        "icons": {
                            "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
                        },
                        "colors": {"open": "#2e7d32"},
                    }
                }
            }
        )
    )
    db = JsonFile(str(db_file))
    result = json_file_db_get_marker_styles(db)
    assert result == {
        "icon_field": "type_of_place",
        "color_field": "status",
        "icons": {
            "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
        },
        "colors": {"open": "#2e7d32"},
    }


def test_json_file_db_get_marker_styles_empty(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {}}))
    db = JsonFile(str(db_file))
    result = json_file_db_get_marker_styles(db)
    assert result == {}


# ------------------------------------------------
# get_initial_view
#
# Every backend returns the raw config untouched; resolve_initial_view fills the blanks in,
# so "declared nothing" has to reach it as {} rather than as a backend's own guess at a view.


def test_json_file_db_get_initial_view(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"initial_view": {"center": [53.37, 22.89], "zoom": 8}}}))
    db = JsonFile(str(db_file))
    assert json_file_db_get_initial_view(db) == {"center": [53.37, 22.89], "zoom": 8}


def test_json_file_db_get_initial_view_empty(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {}}))
    db = JsonFile(str(db_file))
    assert json_file_db_get_initial_view(db) == {}


def test_json_db_get_initial_view():
    db = in_memory_json_db({"initial_view": {"center": [10.0, 20.0], "zoom": 3}})
    assert json_db_get_initial_view(db) == {"center": [10.0, 20.0], "zoom": 3}


def test_json_db_get_initial_view_empty():
    assert json_db_get_initial_view(in_memory_json_db({})) == {}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_initial_view(mock_cli):
    blob = mock_cli.return_value.bucket.return_value.blob.return_value
    blob.download_as_text.return_value = json.dumps(
        {"map": {"initial_view": {"center": [53.37, 22.89], "zoom": 8}}}
    )
    db = GoogleJsonDb("bucket", "blob")
    assert google_json_db_get_initial_view(db) == {"center": [53.37, 22.89], "zoom": 8}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_initial_view_empty(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {}})
    )
    db = GoogleJsonDb("bucket", "blob")
    assert google_json_db_get_initial_view(db) == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_initial_view(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "initial_view": {"center": [53.37, 22.89], "zoom": 8},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    assert mongodb_db_get_initial_view(db) == {"center": [53.37, 22.89], "zoom": 8}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_initial_view_empty(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {"_id": "map_config"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    assert mongodb_db_get_initial_view(db) == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_initial_view_no_config(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    assert mongodb_db_get_initial_view(db) == {}


# Test get_visible_data and get_meta_data for google_json_db
@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_visible_data(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {"visible_data": {"field1": "value1"}, "meta_data": {"meta1": "info1"}}})
    )
    db = GoogleJsonDb("bucket", "blob")
    result = google_json_db_get_visible_data(db)
    assert result == {"field1": "value1"}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_visible_data_empty(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {}})
    )
    db = GoogleJsonDb("bucket", "blob")
    result = google_json_db_get_visible_data(db)
    assert result == {}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_meta_data(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {"visible_data": {"field1": "value1"}, "meta_data": {"meta1": "info1"}}})
    )
    db = GoogleJsonDb("bucket", "blob")
    result = google_json_db_get_meta_data(db)
    assert result == {"meta1": "info1"}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_meta_data_empty(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {}})
    )
    db = GoogleJsonDb("bucket", "blob")
    result = google_json_db_get_meta_data(db)
    assert result == {}


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_marker_styles(mock_cli):
    blob = mock_cli.return_value.bucket.return_value.blob.return_value
    blob.download_as_text.return_value = json.dumps(
        {
            "map": {
                "marker_styles": {
                    "icon_field": "type_of_place",
                    "icons": {
                        "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
                    },
                }
            }
        }
    )
    db = GoogleJsonDb("bucket", "blob")
    result = google_json_db_get_marker_styles(db)
    assert result == {
        "icon_field": "type_of_place",
        "icons": {
            "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
        },
    }


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_marker_styles_empty(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        json.dumps({"map": {}})
    )
    db = GoogleJsonDb("bucket", "blob")
    result = google_json_db_get_marker_styles(db)
    assert result == {}


def test_get_location_from_raw_data_found():
    raw = {"data": [{"uuid": "X", "position": [0, 0]}]}
    Location = create_location_model([], {})
    location: Any = get_location_from_raw_data(raw, "X", Location)
    assert location is not None
    assert location.uuid == "X"
    assert location.position == (0, 0)


def test_get_location_from_raw_data_not_found():
    raw = {"data": [{"uuid": "X", "position": [0, 0]}]}
    Location = create_location_model([], {})
    assert get_location_from_raw_data(raw, "Y", Location) is None


def test_json_db_add_location():
    Location = create_location_model([], {})
    db = in_memory_json_db({"data": []})
    location = {"uuid": "1", "position": [1, 2]}
    json_db_add_location(db, location, Location)
    assert len(db.document.data["data"]) == 1
    assert tuple(db.document.data["data"][0]["position"]) == (1, 2)


def test_json_db_add_duplicate_location():
    Location = create_location_model([], {})
    db = in_memory_json_db({"data": []})
    location = {"uuid": "1", "position": [1, 2]}
    json_db_add_location(db, location, Location)
    with pytest.raises(LocationAlreadyExistsError):
        json_db_add_location(db, location, Location)


def test_json_db_update_location():
    Location = create_location_model([], {})
    db = in_memory_json_db({"data": [{"uuid": "1", "position": [1, 2]}]})
    location_update = {"uuid": "1", "position": [3, 4]}
    json_db_update_location(db, "1", location_update, Location)
    assert tuple(db.document.data["data"][0]["position"]) == (3, 4)


def test_json_db_update_location_not_found():
    Location = create_location_model([], {})
    db = in_memory_json_db({"data": []})
    location_update = {"uuid": "1", "position": [3, 4]}
    with pytest.raises(LocationNotFoundError):
        json_db_update_location(db, "1", location_update, Location)


def test_json_db_delete_location():
    db = in_memory_json_db({"data": [{"uuid": "1", "position": [1, 2]}]})
    json_db_delete_location(db, "1")
    assert db.document.data["data"] == []


def test_json_db_delete_location_not_found():
    db = in_memory_json_db({"data": []})
    with pytest.raises(LocationNotFoundError):
        json_db_delete_location(db, "1")


def test_json_file_db_add_location(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": []}}))
    Location = create_location_model([], {})
    db = JsonFile(str(db_file))
    location_raw = {"uuid": "a", "position": [5, 6]}
    json_file_db_add_location(db, location_raw, Location)
    location = Location.model_validate(location_raw).model_dump(mode="json")
    assert json.loads(db_file.read_text()) == {"map": {"data": [location]}}


def test_json_file_db_write_is_visible_through_the_document(tmp_path):
    """Writes land in the file and in platzky's in-memory document, so neither goes stale."""
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": [], "reports": []}}))
    db = JsonFile(str(db_file))
    Location = create_location_model([], {})

    json_file_db_add_location(db, {"uuid": "a", "position": [5, 6]}, Location)
    json_file_db_add_report(db, {"uuid": "r1", "status": "new"})

    on_disk = json.loads(db_file.read_text())
    assert [point["uuid"] for point in on_disk["map"]["data"]] == ["a"]
    assert on_disk["map"]["reports"] == [{"uuid": "r1", "status": "new"}]
    assert [point["uuid"] for point in db.document.data["map"]["data"]] == ["a"]
    assert db.document.data["map"]["reports"] == [{"uuid": "r1", "status": "new"}]


def test_json_file_db_add_duplicate_location(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": [{"uuid": "a", "position": [5, 6]}]}}))
    Location = create_location_model([], {})
    db = JsonFile(str(db_file))
    location = {"uuid": "a", "position": [5, 6]}
    with pytest.raises(LocationAlreadyExistsError):
        json_file_db_add_location(db, location, Location)


def test_json_file_db_update_location(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": [{"uuid": "a", "position": [5, 6]}]}}))
    Location = create_location_model([], {})
    db = JsonFile(str(db_file))
    location_update_raw = {"uuid": "a", "position": [7, 8]}
    json_file_db_update_location(db, "a", location_update_raw, Location)
    location_update = Location.model_validate(location_update_raw).model_dump(mode="json")
    assert json.loads(db_file.read_text()) == {"map": {"data": [location_update]}}


def test_json_file_db_update_location_not_found(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": []}}))
    Location = create_location_model([], {})
    db = JsonFile(str(db_file))
    location_update_raw = {"uuid": "a", "position": [7, 8]}
    with pytest.raises(LocationNotFoundError):
        json_file_db_update_location(db, "a", location_update_raw, Location)


def test_json_file_db_delete_location(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": [{"uuid": "a", "position": [5, 6]}]}}))
    db = JsonFile(str(db_file))
    json_file_db_delete_location(db, "a")
    assert json.loads(db_file.read_text()) == {"map": {"data": []}}


def test_json_file_db_delete_location_not_found(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"data": []}}))
    db = JsonFile(str(db_file))
    with pytest.raises(LocationNotFoundError):
        json_file_db_delete_location(db, "a")


def test_json_db_add_suggestion():
    db = in_memory_json_db({})
    suggestion = {"uuid": "s1", "foo": "bar"}
    json_db_add_suggestion(db, suggestion)
    assert len(db.document.data["suggestions"]) == 1
    assert db.document.data["suggestions"][0]["status"] == "pending"


def test_json_db_add_duplicate_suggestion():
    db = in_memory_json_db({})
    suggestion = {"uuid": "s1"}
    json_db_add_suggestion(db, suggestion)
    with pytest.raises(AlreadyExistsError):
        json_db_add_suggestion(db, suggestion)


def test_json_db_get_suggestions_filters():
    suggestions = [
        {"uuid": "s1", "status": "pending"},
        {"uuid": "s2", "status": "done"},
    ]
    db = in_memory_json_db({"suggestions": suggestions})
    all_suggestions = json_db_get_suggestions(db, {})
    assert len(all_suggestions) == 2
    pending = json_db_get_suggestions(db, {"status": ["pending"]})
    assert len(pending) == 1 and pending[0]["uuid"] == "s1"


def test_json_db_get_suggestion_by_uuid():
    db = in_memory_json_db({"suggestions": [{"uuid": "s1", "status": "pending"}]})
    suggestion = json_db_get_suggestion(db, "s1")
    assert suggestion is not None and suggestion["uuid"] == "s1"
    assert json_db_get_suggestion(db, "x") is None


def test_json_db_update_suggestion():
    db = in_memory_json_db({"suggestions": [{"uuid": "s1", "status": "pending"}]})
    json_db_update_suggestion(db, "s1", "done")
    assert db.document.data["suggestions"][0]["status"] == "done"


def test_json_db_update_suggestion_not_found():
    db = in_memory_json_db({"suggestions": []})
    with pytest.raises(ValueError):
        json_db_update_suggestion(db, "x", "new")


def test_json_db_update_suggestion_multiple():
    # First element should remain unchanged, second updated
    suggestions = [
        {"uuid": "a", "status": "pending"},
        {"uuid": "b", "status": "pending"},
    ]
    db = in_memory_json_db({"suggestions": [s.copy() for s in suggestions]})
    json_db_update_suggestion(db, "b", "done")
    assert db.document.data["suggestions"][0]["status"] == "pending"
    assert db.document.data["suggestions"][1]["status"] == "done"


def test_json_db_delete_suggestion():
    db = in_memory_json_db({"suggestions": [{"uuid": "s1"}]})
    json_db_delete_suggestion(db, "s1")
    assert db.document.data["suggestions"] == []


def test_json_db_delete_suggestion_not_found():
    db = in_memory_json_db({"suggestions": []})
    with pytest.raises(ValueError):
        json_db_delete_suggestion(db, "s1")


def test_json_file_db_add_suggestion(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": []}}))
    db = JsonFile(str(db_file))
    suggestion_raw = {"uuid": "s1", "foo": "bar"}
    json_file_db_add_suggestion(db, suggestion_raw)
    suggestion = suggestion_raw.copy()
    suggestion["status"] = "pending"
    assert json.loads(db_file.read_text()) == {"map": {"suggestions": [suggestion]}}


def test_json_file_db_add_duplicate_suggestion(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": [{"uuid": "s1"}]}}))
    db = JsonFile(str(db_file))
    suggestion = {"uuid": "s1"}
    with pytest.raises(AlreadyExistsError):
        json_file_db_add_suggestion(db, suggestion)


def test_json_file_db_get_suggestions_filters(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "map": {
                    "suggestions": [
                        {"uuid": "s1", "status": "pending"},
                        {"uuid": "s2", "status": "done"},
                    ]
                }
            }
        )
    )
    db = JsonFile(str(db_file))
    all_suggestions = json_file_db_get_suggestions(db, {})
    assert len(all_suggestions) == 2
    pending = json_file_db_get_suggestions(db, {"status": ["pending"]})
    assert len(pending) == 1 and pending[0]["uuid"] == "s1"


def test_json_file_db_get_suggestion_by_uuid(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": [{"uuid": "s1", "status": "pending"}]}}))
    db = JsonFile(str(db_file))
    suggestion = json_file_db_get_suggestion(db, "s1")
    assert suggestion is not None and suggestion["uuid"] == "s1"
    assert json_file_db_get_suggestion(db, "x") is None


def test_json_file_db_update_suggestion(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": [{"uuid": "s1", "status": "pending"}]}}))
    db = JsonFile(str(db_file))
    json_file_db_update_suggestion(db, "s1", "done")
    suggestion = {"uuid": "s1", "status": "done"}
    assert json.loads(db_file.read_text()) == {"map": {"suggestions": [suggestion]}}


def test_json_file_db_update_suggestion_not_found(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": []}}))
    db = JsonFile(str(db_file))
    with pytest.raises(ValueError):
        json_file_db_update_suggestion(db, "x", "new")


def test_json_file_db_update_suggestion_multiple(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "map": {
                    "suggestions": [
                        {"uuid": "a", "status": "pending"},
                        {"uuid": "b", "status": "pending"},
                    ]
                }
            }
        )
    )
    db = JsonFile(str(db_file))
    json_file_db_update_suggestion(db, "b", "done")
    rec1 = {"uuid": "a", "status": "pending"}
    rec2 = {"uuid": "b", "status": "done"}
    expected = {"map": {"suggestions": [rec1, rec2]}}
    assert json.loads(db_file.read_text()) == expected


def test_json_file_db_delete_suggestion(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": [{"uuid": "s1"}]}}))
    db = JsonFile(str(db_file))
    json_file_db_delete_suggestion(db, "s1")
    assert json.loads(db_file.read_text()) == {"map": {"suggestions": []}}


def test_json_file_db_delete_suggestion_not_found(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": []}}))
    db = JsonFile(str(db_file))
    with pytest.raises(ValueError):
        json_file_db_delete_suggestion(db, "s1")


def test_json_db_add_report():
    db = in_memory_json_db({})
    report = {"uuid": "r1", "status": "new", "priority": "high"}
    json_db_add_report(db, report)
    assert len(db.document.data["reports"]) == 1


def test_json_db_add_duplicate_report():
    db = in_memory_json_db({})
    report = {"uuid": "r1"}
    json_db_add_report(db, report)
    with pytest.raises(ValueError):
        json_db_add_report(db, report)


def test_json_db_get_reports_filters():
    db = in_memory_json_db(
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
    db = in_memory_json_db({"reports": [{"uuid": "r1"}]})
    report = json_db_get_report(db, "r1")
    assert report is not None and report["uuid"] == "r1"
    assert json_db_get_report(db, "x") is None


def test_json_db_update_report_fields():
    db = in_memory_json_db({"reports": [{"uuid": "r1", "status": "new", "priority": "high"}]})
    json_db_update_report(db, "r1", status="done")
    assert db.document.data["reports"][0]["status"] == "done"
    json_db_update_report(db, "r1", priority="low")
    assert db.document.data["reports"][0]["priority"] == "low"
    json_db_update_report(db, "r1", status="new", priority="high")
    assert db.document.data["reports"][0]["status"] == "new"
    assert db.document.data["reports"][0]["priority"] == "high"


def test_json_db_update_report_not_found():
    db = in_memory_json_db({"reports": []})
    report_uuid = "550e8400-e29b-41d4-a716-446655440000"
    with pytest.raises(ReportNotFoundError):
        json_db_update_report(db, report_uuid, status="a")


def test_json_db_update_report_multiple():
    # First report unchanged, second updated
    reports = [
        {"uuid": "r1", "status": "pending", "priority": "low"},
        {"uuid": "r2", "status": "pending", "priority": "low"},
    ]
    db = in_memory_json_db({"reports": [r.copy() for r in reports]})
    json_db_update_report(db, "r2", status="resolved", priority=None)
    assert db.document.data["reports"][0]["status"] == "pending"
    assert db.document.data["reports"][1]["status"] == "resolved"


def test_json_db_delete_report():
    db = in_memory_json_db({"reports": [{"uuid": "r1"}]})
    json_db_delete_report(db, "r1")
    assert db.document.data["reports"] == []


def test_json_db_delete_report_not_found():
    db = in_memory_json_db({"reports": []})
    report_uuid = "550e8400-e29b-41d4-a716-446655440001"
    with pytest.raises(ReportNotFoundError):
        json_db_delete_report(db, report_uuid)


def test_json_file_db_add_report(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"reports": []}}))
    db = JsonFile(str(db_file))
    report = {"uuid": "r1", "status": "new", "priority": "high"}
    json_file_db_add_report(db, report)
    assert json.loads(db_file.read_text()) == {"map": {"reports": [report]}}


def test_json_file_db_add_duplicate_report(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"reports": [{"uuid": "r1"}]}}))
    db = JsonFile(str(db_file))
    report = {"uuid": "r1"}
    with pytest.raises(ValueError):
        json_file_db_add_report(db, report)


def test_json_file_db_get_reports_filters(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "map": {
                    "reports": [
                        {"uuid": "r1", "status": "new", "priority": "high"},
                        {"uuid": "r2", "status": "done", "priority": "low"},
                    ]
                }
            }
        )
    )
    db = JsonFile(str(db_file))
    all_reports = json_file_db_get_reports(db, {})
    assert len(all_reports) == 2
    status_reports = json_file_db_get_reports(db, {"status": ["new"]})
    assert len(status_reports) == 1 and status_reports[0]["uuid"] == "r1"
    priority_reports = json_file_db_get_reports(db, {"priority": ["low"]})
    assert len(priority_reports) == 1 and priority_reports[0]["uuid"] == "r2"


def test_json_file_db_get_report_by_uuid(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"reports": [{"uuid": "r1"}]}}))
    db = JsonFile(str(db_file))
    report = json_file_db_get_report(db, "r1")
    assert report is not None and report["uuid"] == "r1"
    assert json_file_db_get_report(db, "x") is None


def test_json_file_db_update_report_fields(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps({"map": {"reports": [{"uuid": "r1", "status": "new", "priority": "high"}]}})
    )
    db = JsonFile(str(db_file))

    json_file_db_update_report(db, "r1", status="done")
    report = {"uuid": "r1", "status": "done", "priority": "high"}
    assert json.loads(db_file.read_text()) == {"map": {"reports": [report]}}

    json_file_db_update_report(db, "r1", priority="low")
    report = {"uuid": "r1", "status": "done", "priority": "low"}
    assert json.loads(db_file.read_text()) == {"map": {"reports": [report]}}

    json_file_db_update_report(db, "r1", status="new", priority="critical")
    report = {"uuid": "r1", "status": "new", "priority": "critical"}
    assert json.loads(db_file.read_text()) == {"map": {"reports": [report]}}


def test_json_file_db_update_report_not_found(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"reports": []}}))
    db = JsonFile(str(db_file))
    report_uuid = "550e8400-e29b-41d4-a716-446655440002"
    with pytest.raises(ReportNotFoundError):
        json_file_db_update_report(db, report_uuid, status="a")


def test_json_file_db_update_report_multiple(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(
        json.dumps(
            {
                "map": {
                    "reports": [
                        {"uuid": "r1", "status": "pending", "priority": "low"},
                        {"uuid": "r2", "status": "pending", "priority": "low"},
                    ]
                }
            }
        )
    )
    db = JsonFile(str(db_file))
    json_file_db_update_report(db, "r2", priority="critical")
    rec1 = {"uuid": "r1", "status": "pending", "priority": "low"}
    rec2 = {"uuid": "r2", "status": "pending", "priority": "critical"}
    expected = {"map": {"reports": [rec1, rec2]}}
    assert json.loads(db_file.read_text()) == expected


def test_json_file_db_delete_report(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"reports": [{"uuid": "r1"}]}}))
    db = JsonFile(str(db_file))
    json_file_db_delete_report(db, "r1")
    assert json.loads(db_file.read_text()) == {"map": {"reports": []}}


def test_json_file_db_delete_report_not_found(tmp_path):
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"reports": []}}))
    db = JsonFile(str(db_file))
    report_uuid = "550e8400-e29b-41d4-a716-446655440003"
    with pytest.raises(ReportNotFoundError):
        json_file_db_delete_report(db, report_uuid)


def test_dispatch_add_update_delete_location():
    db = in_memory_json_db({"data": []})
    Location = create_location_model([], {})

    loc = {"uuid": "u1", "position": [10, 20]}
    add_location(db, loc, Location)
    assert db.document.data["data"][0]["uuid"] == "u1"

    updated = {"uuid": "u1", "position": [30, 40]}
    update_location(db, "u1", updated, Location)
    assert tuple(db.document.data["data"][0]["position"]) == (30, 40)

    delete_location(db, "u1")
    assert db.document.data["data"] == []


def test_dispatch_add_update_delete_suggestion():
    db = in_memory_json_db({"suggestions": []})

    sugg = {"uuid": "s1", "foo": "bar"}
    add_suggestion(db, sugg)
    assert db.document.data["suggestions"][0]["status"] == "pending"

    update_suggestion(db, "s1", "done")
    assert db.document.data["suggestions"][0]["status"] == "done"

    delete_suggestion(db, "s1")
    assert db.document.data["suggestions"] == []


def test_dispatch_add_update_delete_report():
    db = in_memory_json_db({"reports": []})

    rep = {"uuid": "r1", "status": "new", "priority": "high"}
    add_report(db, rep)
    assert db.document.data["reports"][0]["uuid"] == "r1"

    update_report(db, "r1", status="resolved", priority="low")
    assert db.document.data["reports"][0]["status"] == "resolved"
    assert db.document.data["reports"][0]["priority"] == "low"

    delete_report(db, "r1")
    assert db.document.data["reports"] == []


# MongoDB tests
@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location_obligatory_fields(mock_client):
    mock_db = mongo_database(mock_client)
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
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location_obligatory_fields(db)
    assert result == []


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_data(mock_client):
    mock_db = mongo_database(mock_client)
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
    mock_db = mongo_database(mock_client)
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


# Test get_visible_data and get_meta_data for mongodb_db
@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_visible_data(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "visible_data": {"field1": "value1"},
        "meta_data": {"meta1": "info1"},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_visible_data(db)
    assert result == {"field1": "value1"}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_visible_data_empty(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_visible_data(db)
    assert result == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_visible_data_no_config(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_visible_data(db)
    assert result == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_meta_data(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "visible_data": {"field1": "value1"},
        "meta_data": {"meta1": "info1"},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_meta_data(db)
    assert result == {"meta1": "info1"}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_meta_data_empty(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_meta_data(db)
    assert result == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_meta_data_no_config(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_meta_data(db)
    assert result == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_marker_styles(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "marker_styles": {
            "icon_field": "type_of_place",
            "icons": {
                "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
            },
        },
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_marker_styles(db)
    assert result == {
        "icon_field": "type_of_place",
        "icons": {
            "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
        },
    }


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_marker_styles_empty(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_marker_styles(db)
    assert result == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_marker_styles_no_config(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_marker_styles(db)
    assert result == {}


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.locations.find_one.return_value = {"uuid": "1", "position": [50, 50], "name": "one"}

    Location = create_location_model([], {})
    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location(db, "1", Location)

    assert result is not None
    result = cast(LocationBase, result)
    assert result.uuid == "1"
    assert result.position == (50, 50)
    mock_db.locations.find_one.assert_called_once_with({"uuid": "1"}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_location_not_found(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.locations.find_one.return_value = None

    Location = create_location_model([], {})
    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_location(db, "nonexistent", Location)

    assert result is None


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_location(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.locations.find_one.return_value = None  # No existing location

    Location = create_location_model([], {})
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": "new1", "position": [10, 20]}

    mongodb_db_add_location(db, location_data, Location)

    mock_db.locations.find_one.assert_called_once_with({"uuid": "new1"})
    mock_db.locations.insert_one.assert_called_once()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_duplicate_location(mock_client):
    mock_db = mongo_database(mock_client)
    existing_uuid = "450e8400-e29b-41d4-a716-446655440000"
    mock_db.locations.find_one.return_value = {"uuid": existing_uuid}

    Location = create_location_model([], {})
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": existing_uuid, "position": [10, 20]}

    with pytest.raises(
        LocationAlreadyExistsError, match=f"Location with uuid '{existing_uuid}' already exists"
    ):
        mongodb_db_add_location(db, location_data, Location)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_location(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.matched_count = 1
    mock_db.locations.update_one.return_value = mock_result

    Location = create_location_model([], {})
    db = MongoDB("mongodb://localhost:27017", "test_db")
    location_data = {"uuid": "1", "position": [30, 40]}

    mongodb_db_update_location(db, "1", location_data, Location)

    mock_db.locations.update_one.assert_called_once()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_location_not_found(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.matched_count = 0
    mock_db.locations.update_one.return_value = mock_result

    Location = create_location_model([], {})
    db = MongoDB("mongodb://localhost:27017", "test_db")
    nonexistent_uuid = "850e8400-e29b-41d4-a716-446655440000"
    location_data = {"uuid": nonexistent_uuid, "position": [30, 40]}

    with pytest.raises(
        LocationNotFoundError, match=f"Location with uuid '{nonexistent_uuid}' not found"
    ):
        mongodb_db_update_location(db, nonexistent_uuid, location_data, Location)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_location(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.deleted_count = 1
    mock_db.locations.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_delete_location(db, "1")

    mock_db.locations.delete_one.assert_called_once_with({"uuid": "1"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_location_not_found(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.deleted_count = 0
    mock_db.locations.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    nonexistent_uuid = "750e8400-e29b-41d4-a716-446655440000"

    with pytest.raises(
        LocationNotFoundError, match=f"Location with uuid '{nonexistent_uuid}' not found"
    ):
        mongodb_db_delete_location(db, nonexistent_uuid)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_suggestion(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.suggestions.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    suggestion_data = {"uuid": "s1", "content": "test suggestion"}

    mongodb_db_add_suggestion(db, suggestion_data)

    mock_db.suggestions.find_one.assert_called_once_with({"uuid": "s1"})
    mock_db.suggestions.insert_one.assert_called_once()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_duplicate_suggestion(mock_client):
    mock_db = mongo_database(mock_client)
    s1_uuid = "950e8400-e29b-41d4-a716-446655440000"
    mock_db.suggestions.find_one.return_value = {"uuid": s1_uuid}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    suggestion_data = {"uuid": s1_uuid, "content": "test"}

    with pytest.raises(
        AlreadyExistsError, match=f"Suggestion with uuid '{s1_uuid}' already exists"
    ):
        mongodb_db_add_suggestion(db, suggestion_data)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_suggestions(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.suggestions.find.return_value = [{"uuid": "s1", "status": "pending"}]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_suggestions(db, {"status": ["pending"]})

    expected_query = {"status": {"$in": ["pending"]}}
    mock_db.suggestions.find.assert_called_once_with(expected_query, {"_id": 0})
    assert result == [{"uuid": "s1", "status": "pending"}]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_suggestions_no_status(mock_client):
    mock_db = mongo_database(mock_client)
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
    mock_db = mongo_database(mock_client)
    mock_db.suggestions.find_one.return_value = {"uuid": "s1", "content": "test"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_suggestion(db, "s1")

    assert result == {"uuid": "s1", "content": "test"}
    mock_db.suggestions.find_one.assert_called_once_with({"uuid": "s1"}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_suggestion(mock_client):
    mock_db = mongo_database(mock_client)
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
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.matched_count = 0
    mock_db.suggestions.update_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Suggestion with uuid nonexistent not found"):
        mongodb_db_update_suggestion(db, "nonexistent", "approved")


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_suggestion(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.deleted_count = 1
    mock_db.suggestions.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_delete_suggestion(db, "s1")

    mock_db.suggestions.delete_one.assert_called_once_with({"uuid": "s1"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_suggestion_not_found(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.deleted_count = 0
    mock_db.suggestions.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    with pytest.raises(ValueError, match="Suggestion with uuid nonexistent not found"):
        mongodb_db_delete_suggestion(db, "nonexistent")


def test_json_db_get_categories():
    db = in_memory_json_db(data)
    categories = json_db_get_categories(db)
    assert list(categories) == ["test-category"]


def test_json_file_db_get_categories(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    categories = json_file_db_get_categories(db)
    assert list(categories) == ["test-category"]


def test_json_db_without_categories_serves_locations():
    """A data source with no `categories` at all is a valid setup - a map of plain,
    unfilterable points - so neither listing categories nor querying locations may
    depend on the key being there."""
    uncategorized = {key: value for key, value in data.items() if key != "categories"}
    db = in_memory_json_db(uncategorized)

    assert list(json_db_get_categories(db)) == []
    assert len(json_db_get_locations(db, {}, LocationBase)) == 2


def test_json_file_db_without_categories_serves_locations(tmp_path):
    uncategorized = {key: value for key, value in data.items() if key != "categories"}
    test_file = tmp_path / "test.json"
    test_file.write_text(json.dumps({"map": uncategorized}))

    db = JsonFile(str(test_file))

    assert list(json_file_db_get_categories(db)) == []
    assert len(json_file_db_get_locations(db, {}, LocationBase)) == 2


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_categories(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    categories = google_json_db_get_categories(db)
    assert list(categories) == ["test-category"]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_categories(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    categories = mongodb_db_get_categories(db)
    assert categories == ["test-category"]


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_categories_no_config(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    categories = mongodb_db_get_categories(db)
    assert categories == []


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_categories_no_categories_field(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {"_id": "map_config"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    categories = mongodb_db_get_categories(db)
    assert categories == []


def test_get_categories():
    db = in_memory_json_db(data)
    categories = json_db_get_categories(db)
    assert list(categories) == ["test-category"]


def test_json_db_get_category_data():
    db = in_memory_json_db(data)
    category_data = json_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {},
    }
    assert category_data == expected


def test_json_db_get_category_data_specific_category():
    db = in_memory_json_db(data)
    category_data = json_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {"test-category": "or"},
    }
    assert category_data == expected


def test_json_file_db_get_category_data(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    category_data = json_file_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {},
    }
    assert category_data == expected


def test_json_file_db_get_category_data_specific_category(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    category_data = json_file_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {"test-category": "or"},
    }
    assert category_data == expected


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_category_data(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    category_data = google_json_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {},
    }
    assert category_data == expected


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_category_data_specific_category(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    category_data = google_json_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {"test-category": "or"},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_category_data(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    category_data = mongodb_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_category_data_specific_category(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
    }

    db = MongoDB("mongodb://localhost:27017", "test_db")
    category_data = mongodb_db_get_category_data(db, "test-category")
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {"test-category": "or"},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_category_data_no_config(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    category_data = mongodb_db_get_category_data(db)
    expected = {
        "categories": {},
        "categories_help": [],
        "categories_options_help": {},
        "categories_default_checked": {},
        "categories_filter_mode": {},
    }
    assert category_data == expected


def test_get_category_data():
    db = in_memory_json_db(data)
    category_data = json_db_get_category_data(db)
    expected = {
        "categories": {"test-category": ["searchable", "unsearchable"]},
        "categories_help": ["Help text for categories"],
        "categories_options_help": {"test-category": ["Help for test category"]},
        "categories_default_checked": {"test-category": ["searchable"]},
        "categories_filter_mode": {},
    }
    assert category_data == expected


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.locations.find.return_value = [
        {"uuid": "1", "position": [50, 50]},
        {"uuid": "2", "position": [10, 10]},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query = {"test-category": ["searchable"]}
    locations = list(mongodb_db_get_locations(db, query, LocationBase))

    assert len(locations) == 2
    assert locations[0].uuid == "1"
    assert locations[0].position == (50, 50)
    assert locations[1].uuid == "2"
    assert locations[1].position == (10, 10)

    mock_db.locations.find.assert_called_once_with(
        {"test-category": {"$in": ["searchable"]}},
        {"_id": 0, "uuid": 1, "position": 1, "remark": 1},
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations_and_filter_mode(mock_client):
    """An "and" category must use $all (every selected value), not $in (any)."""
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories_filter_mode": {"amenities": "and"},
    }
    mock_db.locations.find.return_value = [{"uuid": "1", "position": [50, 50]}]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query = {"amenities": ["lighting", "benches"]}
    locations = list(mongodb_db_get_locations(db, query, LocationBase))

    assert len(locations) == 1
    mock_db.locations.find.assert_called_once_with(
        {"amenities": {"$all": ["lighting", "benches"]}},
        {"_id": 0, "uuid": 1, "position": 1, "remark": 1},
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations_threshold_parse_failure_matches_nothing(mock_client):
    """A non-numeric threshold value should match nothing for that category,
    the same as goodmap.filtering's _matches_threshold, rather than silently
    dropping the filter (which would match everything)."""
    mock_db = mongo_database(mock_client)
    mock_db.config.find_one.return_value = {
        "_id": "map_config",
        "categories_filter_mode": {"speed_limit": "threshold"},
    }
    mock_db.locations.find.return_value = []

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query = {"speed_limit": ["not-a-number"]}
    locations = list(mongodb_db_get_locations(db, query, LocationBase))

    assert locations == []
    mock_db.locations.find.assert_called_once_with(
        {"speed_limit": {"$in": []}},
        {"_id": 0, "uuid": 1, "position": 1, "remark": 1},
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations_empty_query(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.locations.find.return_value = []

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query = {"test-category": []}
    locations = list(mongodb_db_get_locations(db, query, LocationBase))

    assert len(locations) == 0
    mock_db.locations.find.assert_called_once_with(
        {}, {"_id": 0, "uuid": 1, "position": 1, "remark": 1}
    )


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_report(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.reports.find_one.return_value = None

    db = MongoDB("mongodb://localhost:27017", "test_db")
    report_data = {"uuid": "r1", "content": "test report"}
    mongodb_db_add_report(db, report_data)

    mock_db.reports.find_one.assert_called_once_with({"uuid": "r1"})
    mock_db.reports.insert_one.assert_called_once_with(report_data)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_add_report_already_exists(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.reports.find_one.return_value = {"uuid": "r1", "content": "existing"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    report_data = {"uuid": "r1", "content": "test report"}

    with pytest.raises(ValueError, match="Report with uuid r1 already exists"):
        mongodb_db_add_report(db, report_data)


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_reports(mock_client):
    mock_db = mongo_database(mock_client)
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
    mock_db = mongo_database(mock_client)
    mock_db.reports.find.return_value = []

    db = MongoDB("mongodb://localhost:27017", "test_db")
    query_params = {}
    reports = mongodb_db_get_reports(db, query_params)

    assert len(reports) == 0
    mock_db.reports.find.assert_called_once_with({}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_report(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.reports.find_one.return_value = {"uuid": "r1", "content": "test"}

    db = MongoDB("mongodb://localhost:27017", "test_db")
    result = mongodb_db_get_report(db, "r1")

    assert result == {"uuid": "r1", "content": "test"}
    mock_db.reports.find_one.assert_called_once_with({"uuid": "r1"}, {"_id": 0})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_report(mock_client):
    mock_db = mongo_database(mock_client)
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
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.matched_count = 0
    mock_db.reports.update_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    report_uuid = "550e8400-e29b-41d4-a716-446655440004"
    with pytest.raises(ReportNotFoundError, match=f"Report with uuid '{report_uuid}' not found"):
        mongodb_db_update_report(db, report_uuid, status="closed")


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_update_report_no_updates(mock_client):
    mock_db = mongo_database(mock_client)

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_update_report(db, "r1")

    mock_db.reports.update_one.assert_not_called()


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_report(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.deleted_count = 1
    mock_db.reports.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")
    mongodb_db_delete_report(db, "r1")

    mock_db.reports.delete_one.assert_called_once_with({"uuid": "r1"})


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_delete_report_not_found(mock_client):
    mock_db = mongo_database(mock_client)
    mock_result = mock.Mock()
    mock_result.deleted_count = 0
    mock_db.reports.delete_one.return_value = mock_result

    db = MongoDB("mongodb://localhost:27017", "test_db")

    report_uuid = "550e8400-e29b-41d4-a716-446655440005"
    with pytest.raises(ReportNotFoundError, match=f"Report with uuid '{report_uuid}' not found"):
        mongodb_db_delete_report(db, report_uuid)


def test_json_file_db_get_locations_paginated(tmp_path):
    test_file = tmp_path / "test.json"
    test_file.write_text(data_json)

    db = JsonFile(str(test_file))
    Location = create_location_model([], {})

    query = {"page": ["1"], "per_page": ["2"], "sort_by": ["name"], "sort_order": ["asc"]}
    result = json_file_db_get_locations_paginated(db, query, Location)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) <= 2
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["per_page"] == 2


@mock.patch("platzky.db.google_json_db.Client")
def test_google_json_db_get_locations_paginated(mock_client):
    mock_client.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "file.json")
    Location = create_location_model([], {})

    query = {"page": ["1"], "per_page": ["2"]}
    result = google_json_db_get_locations_paginated(db, query, Location)

    assert "items" in result
    assert "pagination" in result
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["per_page"] == 2


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_locations_paginated(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.locations.count_documents.return_value = 5
    mock_db.locations.aggregate.return_value = [
        {"uuid": "1", "name": "test1", "position": [50, 50]},
        {"uuid": "2", "name": "test2", "position": [10, 10]},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")
    Location = create_location_model([], {})

    query = {"page": ["1"], "per_page": ["2"], "sort_by": ["name"], "sort_order": ["desc"]}
    result = mongodb_db_get_locations_paginated(db, query, Location)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) == 2
    assert result["pagination"]["total"] == 5
    assert result["pagination"]["page"] == 1
    assert result["pagination"]["per_page"] == 2


def test_json_file_db_get_suggestions_paginated(tmp_path):
    test_file = tmp_path / "test.json"
    test_data = {
        "map": {
            "suggestions": [
                {"uuid": "s1", "status": "pending", "created_at": "2024-01-01"},
                {"uuid": "s2", "status": "done", "created_at": "2024-01-02"},
                {"uuid": "s3", "status": "pending", "created_at": "2024-01-03"},
            ]
        }
    }
    test_file.write_text(json.dumps(test_data))

    db = JsonFile(str(test_file))

    query = {
        "page": ["1"],
        "per_page": ["2"],
        "status": ["pending"],
        "sort_by": ["created_at"],
        "sort_order": ["desc"],
    }
    result = json_file_db_get_suggestions_paginated(db, query)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) <= 2
    assert all(item["status"] == "pending" for item in result["items"])


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_suggestions_paginated(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.suggestions.count_documents.return_value = 3
    mock_db.suggestions.aggregate.return_value = [
        {"uuid": "s1", "status": "pending"},
        {"uuid": "s2", "status": "pending"},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")

    query = {"page": ["1"], "per_page": ["2"], "status": ["pending"]}
    result = mongodb_db_get_suggestions_paginated(db, query)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) == 2
    assert result["pagination"]["total"] == 3


def test_json_file_db_get_reports_paginated(tmp_path):
    test_file = tmp_path / "test.json"
    test_data = {
        "map": {
            "reports": [
                {"uuid": "r1", "status": "new", "priority": "high", "created_at": "2024-01-01"},
                {"uuid": "r2", "status": "open", "priority": "low", "created_at": "2024-01-02"},
                {"uuid": "r3", "status": "new", "priority": "critical", "created_at": "2024-01-03"},
            ]
        }
    }
    test_file.write_text(json.dumps(test_data))

    db = JsonFile(str(test_file))

    query = {
        "page": ["1"],
        "per_page": ["2"],
        "status": ["new"],
        "priority": ["high", "critical"],
        "sort_by": ["created_at"],
        "sort_order": ["asc"],
    }
    result = json_file_db_get_reports_paginated(db, query)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) <= 2
    assert all(item["status"] == "new" for item in result["items"])
    assert all(item["priority"] in ["high", "critical"] for item in result["items"])


@mock.patch("platzky.db.mongodb_db.MongoClient")
def test_mongodb_db_get_reports_paginated(mock_client):
    mock_db = mongo_database(mock_client)
    mock_db.reports.count_documents.return_value = 4
    mock_db.reports.aggregate.return_value = [
        {"uuid": "r1", "status": "new", "priority": "high"},
        {"uuid": "r2", "status": "new", "priority": "critical"},
    ]

    db = MongoDB("mongodb://localhost:27017", "test_db")

    query = {"page": ["1"], "per_page": ["2"], "status": ["new"], "priority": ["high", "critical"]}
    result = mongodb_db_get_reports_paginated(db, query)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) == 2
    assert result["pagination"]["total"] == 4


# Test missing coverage lines for pagination parameter parsing
def test_parse_pagination_params_edge_cases():
    # Import the module to access the private function dynamically
    import goodmap.db as db_module

    parse_params = getattr(db_module, "__parse_pagination_params")

    # Test ValueError/IndexError/TypeError for page parameter
    page, per_page, _, _ = parse_params({"page": ["invalid"]})
    assert page == 1

    page, per_page, _, _ = parse_params({"page": []})
    assert page == 1

    page, per_page, _, _ = parse_params({"page": [None]})
    assert page == 1

    # Test per_page = "all"
    page, per_page, _, _ = parse_params({"per_page": ["all"]})
    assert per_page is None

    # Test ValueError/TypeError for per_page parameter
    page, per_page, _, _ = parse_params({"per_page": ["invalid"]})
    assert per_page == 20

    page, per_page, _, _ = parse_params({"per_page": [None]})
    assert per_page == 20


def test_build_pagination_response_per_page_none():
    # Import the module to access the private function dynamically
    import goodmap.db as db_module

    build_response = getattr(db_module, "__build_pagination_response")

    # Test when per_page is None
    result = build_response(["item1", "item2"], 2, 1, None)
    pagination = result["pagination"]
    assert pagination["total_pages"] == 1
    assert pagination["per_page"] == 2


# Test json_db pagination functions that were missing coverage
def test_json_db_get_locations_paginated():
    from goodmap.db import json_db_get_locations_paginated

    db = in_memory_json_db(data)
    Location = create_location_model([], {})

    # Test with sorting by name
    query = {"page": ["1"], "per_page": ["10"], "sort_by": ["name"], "sort_order": ["desc"]}
    result = json_db_get_locations_paginated(db, query, Location)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) == 2

    # Test without per_page
    query = {"page": ["1"], "sort_by": ["name"]}
    result = json_db_get_locations_paginated(db, query, Location)
    assert len(result["items"]) == 2

    # Test with hasattr check for model_dump
    assert all("uuid" in item for item in result["items"])


def test_json_db_get_suggestions_paginated():
    from goodmap.db import json_db_get_suggestions_paginated

    suggestions_data = {
        "suggestions": [
            {"uuid": "s1", "status": "pending", "created_at": "2024-01-01"},
            {"uuid": "s2", "status": "done", "created_at": "2024-01-02"},
            {"uuid": "s3", "status": "pending", "created_at": "2024-01-03"},
        ]
    }
    db = in_memory_json_db(suggestions_data)

    # Test with status filtering and sorting
    query = {
        "page": ["1"],
        "per_page": ["2"],
        "status": ["pending"],
        "sort_by": ["created_at"],
        "sort_order": ["desc"],
    }
    result = json_db_get_suggestions_paginated(db, query)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) <= 2
    assert all(item["status"] == "pending" for item in result["items"])

    # Test without per_page
    query = {"status": ["pending"]}
    result = json_db_get_suggestions_paginated(db, query)
    assert len(result["items"]) == 2


def test_json_db_get_reports_paginated():
    from goodmap.db import json_db_get_reports_paginated

    reports_data = {
        "reports": [
            {"uuid": "r1", "status": "new", "priority": "high", "created_at": "2024-01-01"},
            {"uuid": "r2", "status": "open", "priority": "low", "created_at": "2024-01-02"},
            {"uuid": "r3", "status": "new", "priority": "critical", "created_at": "2024-01-03"},
        ]
    }
    db = in_memory_json_db(reports_data)

    # Test with status and priority filtering, sorting
    query = {
        "page": ["1"],
        "per_page": ["2"],
        "status": ["new"],
        "priority": ["high", "critical"],
        "sort_by": ["created_at"],
        "sort_order": ["asc"],
    }
    result = json_db_get_reports_paginated(db, query)

    assert "items" in result
    assert "pagination" in result
    assert len(result["items"]) <= 2
    assert all(item["status"] == "new" for item in result["items"])
    assert all(item["priority"] in ["high", "critical"] for item in result["items"])

    # Test without per_page
    query = {"status": ["new"]}
    result = json_db_get_reports_paginated(db, query)
    assert len(result["items"]) == 2


# Test sorting functionality in other pagination functions
def test_google_json_db_sorting_edge_cases():
    from goodmap.db import google_json_db_get_locations_paginated

    # Test sorting when item has no 'name' attribute
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")
        Location = create_location_model([], {})

        # Test sort by non-existent field
        query = {
            "page": ["1"],
            "per_page": ["2"],
            "sort_by": ["non_existent_field"],
            "sort_order": ["asc"],
        }
        result = google_json_db_get_locations_paginated(db, query, Location)

        assert "items" in result
        assert "pagination" in result


def test_mongodb_sorting_edge_cases():
    from goodmap.db import (
        mongodb_db_get_locations_paginated,
        mongodb_db_get_reports_paginated,
        mongodb_db_get_suggestions_paginated,
    )

    # Test MongoDB sorting functionality
    with mock.patch("platzky.db.mongodb_db.MongoClient") as mock_client:
        mock_db = mongo_database(mock_client)
        mock_db.locations.count_documents.return_value = 2
        mock_db.locations.aggregate.return_value = [
            {"uuid": "1", "name": "test1", "position": [50, 50]},
            {"uuid": "2", "name": "test2", "position": [10, 10]},
        ]

        db = MongoDB("mongodb://localhost:27017", "test_db")
        Location = create_location_model([], {})

        # Test sort_direction logic
        query = {"page": ["1"], "per_page": ["2"], "sort_by": ["name"], "sort_order": ["desc"]}
        mongodb_db_get_locations_paginated(db, query, Location)

        # Verify the aggregation pipeline includes correct sort direction
        calls = mock_db.locations.aggregate.call_args_list
        pipeline = calls[0][0][0]
        sort_stage = next((stage for stage in pipeline if "$sort" in stage), None)
        assert sort_stage is not None
        assert sort_stage["$sort"]["name"] == -1  # desc = -1

        # Test suggestions pagination sorting
        mock_db.suggestions.count_documents.return_value = 1
        mock_db.suggestions.aggregate.return_value = [{"uuid": "s1", "status": "pending"}]

        query = {"sort_by": ["status"], "sort_order": ["asc"]}
        mongodb_db_get_suggestions_paginated(db, query)

        # Test reports pagination sorting
        mock_db.reports.count_documents.return_value = 1
        mock_db.reports.aggregate.return_value = [{"uuid": "r1", "status": "new"}]

        query = {"sort_by": ["priority"], "sort_order": ["desc"]}
        mongodb_db_get_reports_paginated(db, query)


# Test additional missing coverage lines
def test_google_json_db_pagination_no_per_page():
    from goodmap.db import google_json_db_get_locations_paginated

    # Test lines 344, 350 - no per_page and no hasattr case
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")
        Location = create_location_model([], {})

        # Test without per_page
        query = {"page": ["1"]}  # No per_page specified
        result = google_json_db_get_locations_paginated(db, query, Location)
        assert len(result["items"]) == 2

        # Test line 350 - when items don't have model_dump (create raw dict items)
        query = {"page": ["1"], "per_page": ["10"]}
        result = google_json_db_get_locations_paginated(db, query, Location)
        # Items will be Location objects with model_dump, so this tests line 347-348


def test_json_db_pagination_no_per_page():
    from goodmap.db import json_db_get_locations_paginated

    db = in_memory_json_db(data)
    Location = create_location_model([], {})

    # Test lines 384, 390 - no per_page
    query = {"page": ["1"]}  # No per_page specified
    result = json_db_get_locations_paginated(db, query, Location)
    assert len(result["items"]) == 2


def test_json_file_pagination_no_hasattr(tmp_path):
    from goodmap.db import json_file_db_get_locations_paginated

    # Mock to return raw dict data instead of Location objects
    db_file = tmp_path / "db.json"
    db_file.write_text(data_json)
    db = JsonFile(str(db_file))

    # Test get_sort_key when item has name attribute
    query = {"page": ["1"], "per_page": ["10"], "sort_by": ["name"], "sort_order": ["asc"]}
    result = json_file_db_get_locations_paginated(db, query, create_location_model([], {}))
    assert "items" in result

    # Test get_sort_key when sort_by is not 'name'
    query = {"page": ["1"], "per_page": ["10"], "sort_by": ["uuid"], "sort_order": ["asc"]}
    result = json_file_db_get_locations_paginated(db, query, create_location_model([], {}))
    assert "items" in result


def test_suggestions_pagination_no_per_page():
    from goodmap.db import json_db_get_suggestions_paginated

    suggestions_data = {"suggestions": [{"uuid": "s1", "status": "pending"}]}
    db = in_memory_json_db(suggestions_data)

    # Test line 700 - no per_page
    query = {"page": ["1"]}
    result = json_db_get_suggestions_paginated(db, query)
    assert len(result["items"]) == 1


def test_mongodb_suggestions_pagination_sorting():
    from goodmap.db import mongodb_db_get_suggestions_paginated

    # Test line 1058 - MongoDB suggestions sort_direction logic
    with mock.patch("platzky.db.mongodb_db.MongoClient") as mock_client:
        mock_db = mongo_database(mock_client)
        mock_db.suggestions.count_documents.return_value = 1
        mock_db.suggestions.aggregate.return_value = [{"uuid": "s1", "status": "pending"}]

        db = MongoDB("mongodb://localhost:27017", "test_db")

        # Test ascending sort
        query = {"sort_by": ["status"], "sort_order": ["asc"]}
        mongodb_db_get_suggestions_paginated(db, query)

        # Verify the aggregation pipeline includes correct sort direction
        calls = mock_db.suggestions.aggregate.call_args_list
        pipeline = calls[0][0][0]
        sort_stage = next((stage for stage in pipeline if "$sort" in stage), None)
        assert sort_stage is not None
        assert sort_stage["$sort"]["status"] == 1  # asc = 1


def test_reports_pagination_no_per_page():
    from goodmap.db import json_db_get_reports_paginated

    reports_data = {"reports": [{"uuid": "r1", "status": "new"}]}
    db = in_memory_json_db(reports_data)

    # Test line 1000 - no per_page
    query = {"page": ["1"]}
    result = json_db_get_reports_paginated(db, query)
    assert len(result["items"]) == 1


def test_json_file_pagination_no_per_page(tmp_path):
    from goodmap.db import json_file_db_get_locations_paginated

    # Test line 427 - no per_page in json_file_db
    db_file = tmp_path / "db.json"
    db_file.write_text(data_json)
    db = JsonFile(str(db_file))
    Location = create_location_model([], {})

    query = {"page": ["1"]}  # No per_page
    result = json_file_db_get_locations_paginated(db, query, Location)
    assert len(result["items"]) == 2


# Test very specific missing lines by calling functions directly
def test_specific_missing_lines(tmp_path):
    from goodmap.db import (
        google_json_db_get_locations_paginated,
        json_db_get_locations_paginated,
        json_db_get_reports_paginated,
        json_db_get_suggestions_paginated,
        json_file_db_get_locations_paginated,
        json_file_db_get_suggestions_paginated,
        mongodb_db_get_suggestions_paginated,
    )

    # Test line 344 - google_json_db when per_page is None
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")
        Location = create_location_model([], {})

        # Force per_page to be None by using "all"
        query = {"per_page": ["all"], "page": ["1"]}
        result = google_json_db_get_locations_paginated(db, query, Location)
        assert len(result["items"]) == 2

    # Test line 350 - google_json_db when no hasattr model_dump (need raw dicts)
    with mock.patch("platzky.db.google_json_db.Client") as mock_client:
        mock_blob = mock_client.return_value.bucket.return_value.blob.return_value
        mock_blob.download_as_text.return_value = data_json
        db = GoogleJsonDb("bucket", "file.json")

        # Mock get_locations_list_from_raw_data to return raw dicts without model_dump
        with mock.patch("goodmap.db.get_locations_list_from_raw_data") as mock_get_locs:
            mock_get_locs.return_value = [{"uuid": "1", "position": [50, 50]}]  # Raw dicts
            query = {"per_page": ["1"], "page": ["1"]}
            Location = create_location_model([], {})
            result = google_json_db_get_locations_paginated(db, query, Location)
            assert len(result["items"]) == 1

    # Test line 384 - json_db when per_page is None
    db = in_memory_json_db(data)
    Location = create_location_model([], {})
    query = {"per_page": ["all"], "page": ["1"]}
    result = json_db_get_locations_paginated(db, query, Location)
    assert len(result["items"]) == 2

    # Test line 390 - json_db when no hasattr model_dump
    with mock.patch("goodmap.db.get_locations_list_from_raw_data") as mock_get_locs:
        mock_get_locs.return_value = [{"uuid": "1", "position": [50, 50]}]  # Raw dicts
        query = {"per_page": ["1"], "page": ["1"]}
        result = json_db_get_locations_paginated(db, query, Location)
        assert len(result["items"]) == 1

    # Test line 427 - json_file_db when per_page is None
    db_file = tmp_path / "db.json"
    db_file.write_text(data_json)
    db = JsonFile(str(db_file))
    Location = create_location_model([], {})
    query = {"per_page": ["all"], "page": ["1"]}
    result = json_file_db_get_locations_paginated(db, query, Location)
    assert len(result["items"]) == 2

    # Test line 433 - json_file_db when no hasattr model_dump
    db_file = tmp_path / "db.json"
    db_file.write_text(data_json)
    with mock.patch("goodmap.db.get_locations_list_from_raw_data") as mock_get_locs:
        mock_get_locs.return_value = [{"uuid": "1", "position": [50, 50]}]  # Raw dicts
        db = JsonFile(str(db_file))
        Location = create_location_model([], {})
        query = {"per_page": ["1"], "page": ["1"]}
        result = json_file_db_get_locations_paginated(db, query, Location)
        assert len(result["items"]) == 1

    # Test line 700 - json_db_get_suggestions when per_page is None
    suggestions_data = {"suggestions": [{"uuid": "s1", "status": "pending"}]}
    db = in_memory_json_db(suggestions_data)
    query = {"per_page": ["all"], "page": ["1"]}
    result = json_db_get_suggestions_paginated(db, query)
    assert len(result["items"]) == 1

    # Test line 750 - json_file_db_get_suggestions when per_page is None
    db_file = tmp_path / "db.json"
    db_file.write_text(json.dumps({"map": {"suggestions": [{"uuid": "s1"}]}}))
    db = JsonFile(str(db_file))
    query = {"per_page": ["all"], "page": ["1"]}
    result = json_file_db_get_suggestions_paginated(db, query)
    assert len(result["items"]) == 1

    # Test line 1000 - json_db_get_reports when per_page is None
    reports_data = {"reports": [{"uuid": "r1", "status": "new"}]}
    db = in_memory_json_db(reports_data)
    query = {"per_page": ["all"], "page": ["1"]}
    result = json_db_get_reports_paginated(db, query)
    assert len(result["items"]) == 1

    # Test line 1058 - mongodb suggestions sort ascending
    with mock.patch("platzky.db.mongodb_db.MongoClient") as mock_client:
        mock_db = mongo_database(mock_client)
        mock_db.suggestions.count_documents.return_value = 1
        mock_db.suggestions.aggregate.return_value = [{"uuid": "s1", "status": "pending"}]

        db = MongoDB("mongodb://localhost:27017", "test_db")

        # Test ascending sort (sort_direction = 1)
        query = {"sort_by": ["status"], "sort_order": ["asc"]}
        result = mongodb_db_get_suggestions_paginated(db, query)
        assert len(result["items"]) == 1

    # Test line 474 - json_file_db when no hasattr model_dump with sorting
    db_file = tmp_path / "db.json"
    db_file.write_text(data_json)
    with mock.patch("goodmap.db.get_locations_list_from_raw_data") as mock_get_locs:
        mock_get_locs.return_value = [{"uuid": "1", "position": [50, 50]}]  # Raw dicts
        db = JsonFile(str(db_file))
        Location = create_location_model([], {})
        query = {"per_page": ["1"], "page": ["1"], "sort_by": ["name"]}
        result = json_file_db_get_locations_paginated(db, query, Location)
        assert len(result["items"]) == 1


# Test the two remaining missing lines for 100% coverage
def test_remaining_missing_coverage_lines(tmp_path):
    # Test line 474 - MongoDB case when locations list is empty, serialized_locations = locations
    from goodmap.db import (
        json_file_db_get_reports_paginated,
        mongodb_db_get_locations_paginated,
    )

    with mock.patch("platzky.db.mongodb_db.MongoClient") as mock_client:
        mock_db = mongo_database(mock_client)
        mock_db.locations.count_documents.return_value = 0  # Empty result
        mock_db.locations.aggregate.return_value = []  # Empty locations list

        db = MongoDB("mongodb://localhost:27017", "test_db")
        Location = create_location_model([], {})

        query = {"per_page": ["1"], "page": ["1"]}
        result = mongodb_db_get_locations_paginated(db, query, Location)
        assert len(result["items"]) == 0  # This hits line 474: serialized_locations = locations

    # Test line 1058 - when per_page is None in reports pagination (json_file_db)
    reports_json = json.dumps({"map": {"reports": [{"uuid": "r1", "status": "new"}]}})
    db_file = tmp_path / "db.json"
    db_file.write_text(reports_json)
    db = JsonFile(str(db_file))

    # Use per_page="all" to make per_page None, triggering line 1058
    query = {"per_page": ["all"], "page": ["1"]}
    result = json_file_db_get_reports_paginated(db, query)
    assert len(result["items"]) == 1  # This hits line 1058: items = reports


def test_pagination_helper_error_handling():
    """Test error handling in PaginationHelper.create_paginated_response"""
    from goodmap.db import PaginationHelper

    # Test invalid page parameter
    query = {"page": ["invalid"]}
    result = PaginationHelper.create_paginated_response([], query)
    assert result["pagination"]["page"] == 1  # Should default to 1

    # Test invalid per_page parameter
    query = {"per_page": ["invalid"]}
    result = PaginationHelper.create_paginated_response([], query)
    assert result["pagination"]["per_page"] == 20  # Should default to 20

    # Test custom filter extraction
    def custom_extract(query):
        return {"custom_field": query.get("custom", ["default"])[0]}

    query = {"custom": ["test_value"]}
    items = [{"name": "test", "custom_field": "test_value"}]
    result = PaginationHelper.create_paginated_response(items, query, custom_extract)
    assert len(result["items"]) == 1  # Custom filter should pass the item


def test_json_file_db_sorted_page_leaves_the_document_order_alone(tmp_path):
    path = tmp_path / "db.json"
    reports = [{"uuid": "a", "status": "pending"}, {"uuid": "b", "status": "pending"}]
    path.write_text(json.dumps({"map": {"reports": reports}}))
    db = JsonFile(str(path))
    queries = goodmap_queries(db, LocationBase)

    page = queries.get_reports_paginated({"sort_by": ["uuid"], "sort_order": ["desc"]})

    assert [r["uuid"] for r in page["items"]] == ["b", "a"]
    assert [r["uuid"] for r in db.document.data["map"]["reports"]] == ["a", "b"]

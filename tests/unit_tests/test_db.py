import json
from unittest import mock

from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_db import Json
from platzky.db.json_file_db import JsonFile

from goodmap.data_models.location import create_location_model
from goodmap.db import extend_db_with_goodmap_queries, get_location_obligatory_fields

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

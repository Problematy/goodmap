import json
from unittest import mock

from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_db import Json
from platzky.db.json_file_db import JsonFile

from goodmap.data_models.location import LocationBase
from goodmap.db import goodmap_db_extended_app

expected_data = {"data": [{"position": [50, 50], "UUID": "1"}, {"position": [10, 10], "UUID": "2"}]}
data_json = json.dumps({"map": expected_data})


def initialize_and_assert_db(db, data):
    goodmap_db_extended_app(db, LocationBase)
    assert db.get_location("1") == LocationBase(position=(50, 50), UUID="1")
    assert len(db.get_locations()) == 2
    assert db.get_data() == data


def test_goodmap_json_db_extended():
    db = Json(expected_data)
    initialize_and_assert_db(db, expected_data)


@mock.patch("builtins.open", mock.mock_open(read_data=data_json))
def test_goodmap_json_db_file_extended():
    db = JsonFile("/fake/path/file.json")
    initialize_and_assert_db(db, expected_data)


@mock.patch("platzky.db.google_json_db.Client")
def test_goodmap_google_json_db_extended(mock_cli):
    mock_cli.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = (
        data_json
    )
    db = GoogleJsonDb("bucket", "blob")
    initialize_and_assert_db(db, expected_data)

from unittest import mock

from goodmap.data_models.location import LocationBase
from goodmap.db import goodmap_db_extended_app
from platzky.db.json_db import Json
from platzky.db.json_file_db import JsonFile
from platzky.db.google_json_db import GoogleJsonDb

def test_goodmap_json_db_extended():
    data = {"data":[{"position": [50, 50], "UUID": "1"}, {"position": [10, 10], "UUID": "2"}]}
    db = Json(data)
    goodmap_db_extended_app(db, LocationBase)
    assert db.get_location("1") == LocationBase(position=(50, 50), UUID="1")
    assert len(db.get_locations()) == 2
    assert db.get_data() == data


@mock.patch("builtins.open", mock.mock_open(read_data='{"map":{"data":[{"position": [50, 50], "UUID": "1"}, {"position": [10, 10], "UUID": "2"}]}}'))
def test_goodmap_json_db_file_extended():
    expected_data = {"data":[{"position": [50, 50], "UUID": "1"}, {"position": [10, 10], "UUID": "2"}]}
    db = JsonFile("/fake/path/file.json")
    goodmap_db_extended_app(db, LocationBase)
    assert db.get_location("1") == LocationBase(position=(50, 50), UUID="1")
    assert len(db.get_locations()) == 2
    assert db.get_data() == expected_data


@mock.patch("platzky.db.google_json_db.Client")
def test_goodmap_google_json_db_extended(mock_client):
    mock_client.return_value.bucket.return_value.blob.return_value.download_as_text.return_value = '{"map":{"data":[{"position": [50, 50], "UUID": "1"}, {"position": [10, 10], "UUID": "2"}]}}'
    db = GoogleJsonDb("bucket", "blob")
    goodmap_db_extended_app(db, LocationBase)
    assert db.get_location("1") == LocationBase(position=(50, 50), UUID="1")
    assert len(db.get_locations()) == 2
    assert db.get_data() == {"data":[{"position": [50, 50], "UUID": "1"}, {"position": [10, 10], "UUID": "2"}]}

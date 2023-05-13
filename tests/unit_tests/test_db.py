from platzky.db.json_db import Json
from platzky.db.google_json_db import GoogleJsonDb


def test_failed_get_page():
    dbs = [Json({"pages": []}), GoogleJsonDb("foo", "bar")]

    for db in dbs:
        assert db.get_page("foo") is None


def test_get_page():
    dbs = [Json({"pages": [{"slug": "foo"}]}), GoogleJsonDb("foo", "bar")]

    for db in dbs:
        assert db.get_page("foo") is not None
        assert db.get_page("foo")["slug"] == "foo"

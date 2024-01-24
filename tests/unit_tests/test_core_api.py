import json
from unittest import mock
from unittest.mock import MagicMock

import pytest
from flask import Flask

from goodmap.platzky.config import LanguageConfig, Languages, languages_dict
from goodmap.core_api import core_pages


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
    b = LanguageConfig(name="English", flag="uk")
    a = Languages({"en": b})
    languages = languages_dict(a)
    app = Flask(__name__)
    db_mock.get_data.return_value = {
        "categories": {"test-category": ["test", "test2"]},
        "locations": [],
        "data": [
            {
                "name": "test",
                "position": [50, 50],
                "test-category": "test",
                "type_of_place": "test-place",
            }
        ],
        "meta_data": {"test": "test"},
        "visible_data": ["name"],
    }
    app.register_blueprint(core_pages(db_mock, languages, notifier_function, lambda: "csrf"))
    return app.test_client()


def test_reporting_location_is_sending_message_with_name_and_coordinates(
    test_app, notifier_function
):
    data = {"id": "location-id", "description": "some error"}
    headers = {"Content-Type": "application/json"}
    response = test_app.post("/api/report-location", data=json.dumps(data), headers=headers)
    notification_message = str(notifier_function.call_args)

    assert "id" in notification_message
    assert "some error" in notification_message
    assert response.status_code == 200


def test_reporting_returns_error_when_wrong_json(test_app, notifier_function):
    data = {"name": "location-id", "coordinates": 50}
    headers = {"Content-Type": "application/json"}
    response = test_app.post("/api/report-location", data=json.dumps(data), headers=headers)
    assert response.status_code == 400
    assert "Error" in response.json["message"]


def test_language_endpoint_returns_languages(test_app):
    response = test_app.get("/api/languages")
    assert response.status_code == 200
    # TODO domain should not be in response if its None
    assert response.json == {"en": {"domain": None, "name": "English", "flag": "uk"}}


# TODO change db_mock of below tests to real json db


@mock.patch("goodmap.core_api.gettext", fake_translation)
def test_categories_endpoint_returns_categories(test_app):
    # make gettext used in flask_babel return the same string as the input
    response = test_app.get("/api/categories")
    assert response.status_code == 200
    assert response.json == [["test-category", "test-category-translated"]]


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("goodmap.formatter.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_data_endpoint_returns_data(test_app):
    response = test_app.get("/api/data")
    assert response.status_code == 200
    assert response.json == [
        {
            "data": {"name-translated": "test-translated"},
            "metadata": {},
            "position": [50, 50],
            "subtitle": "test-place-translated",
            "title": "test",
        }
    ]


@mock.patch("goodmap.core_api.gettext", fake_translation)
@mock.patch("goodmap.formatter.gettext", fake_translation)
@mock.patch("flask_babel.gettext", fake_translation)
def test_data_endpoint_returns_filtered_data(test_app):
    response = test_app.get("/api/data?test-category=test")
    assert response.status_code == 200
    assert response.json == [
        {
            "data": {"name-translated": "test-translated"},
            "metadata": {},
            "position": [50, 50],
            "subtitle": "test-place-translated",
            "title": "test",
        }
    ]


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

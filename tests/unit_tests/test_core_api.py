import json
from unittest.mock import MagicMock

import pytest
from flask import Flask

from goodmap.config import LanguageConfig, Languages, languages_dict
from goodmap.core_api import core_pages


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
    app.register_blueprint(core_pages(db_mock, languages, notifier_function))
    return app.test_client()


def test_reporting_location_is_sending_message_with_name_and_coordinates(
    test_app, notifier_function
):
    data = {"name": "location-name", "coordinates": [50, 50]}
    headers = {"Content-Type": "application/json"}
    response = test_app.post("/api/report_location", data=json.dumps(data), headers=headers)
    notification_message = str(notifier_function.call_args)

    assert "location-name" in notification_message
    assert "(50.0, 50.0)" in notification_message
    assert response.status_code == 200

def test_language_endpoint_returns_languages(test_app):
    response = test_app.get("/api/languages")
    assert response.status_code == 200
    #TODO domain should not be in response
    assert response.json == {"en": {"domain":None,"name": "English", "flag": "uk"}}

#TODO change db_mock of below tests to real json db
def test_data_endpoint_returns_data(test_app, db_mock):
    response = test_app.get("/api/data")
    db_mock.get_data.assert_called_once()
    assert response.status_code == 200

def test_categories_endpoint_returns_categories(test_app, db_mock):
    response = test_app.get("/api/categories")
    db_mock.get_data.assert_called_once()
    assert response.status_code == 200

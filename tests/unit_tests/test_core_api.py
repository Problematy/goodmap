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
def test_app(notifier_function):
    db_mock = MagicMock()
    languages = languages_dict(Languages({"en": LanguageConfig(name="English", flag="uk")}))
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

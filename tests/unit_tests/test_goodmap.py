from unittest.mock import MagicMock, patch

import pytest
from platzky.config import Config
from platzky.db.json_db import JsonDbConfig

from goodmap import goodmap

config = Config(
    APP_NAME="test",
    SECRET_KEY="test",
    DB=JsonDbConfig(DATA={}, TYPE="json"),
)


@pytest.mark.skip_coverage
def test_create_app():
    goodmap.create_app_from_config(config)


def test_create_app_from_config():
    with patch("platzky.platzky.create_app_from_config", MagicMock()) as mock_platzky_app_creation:
        with patch("goodmap.goodmap.get_data", MagicMock()) as mock_get_data:
            goodmap.create_app_from_config(config)

            mock_platzky_app_creation.assert_called_once_with(config)
            mock_get_data.assert_called_once()

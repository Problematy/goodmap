from unittest.mock import MagicMock, patch

import pytest

from goodmap import goodmap
from goodmap.config import Config
from goodmap.platzky.db.json_db import JsonDbConfig

config = Config(
    APP_NAME="test",
    SECRET_KEY="test",
    DB=JsonDbConfig(DATA={}, TYPE="json_db"),
)


@pytest.mark.skip_coverage
def test_create_app():
    goodmap.create_app_from_config(config)


def test_create_app_from_config():
    with patch(
        "goodmap.goodmap.platzky.create_app_from_config", MagicMock()
    ) as mock_platzky_app_creation, patch(
        "goodmap.goodmap.get_db_specific_get_data", MagicMock()
    ) as mock_get_data:
        goodmap.create_app_from_config(config)

        mock_platzky_app_creation.assert_called_once_with(config)
        mock_get_data.assert_called_once()

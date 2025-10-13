from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from platzky.db.json_db import JsonDbConfig

from goodmap import goodmap
from goodmap.config import GoodmapConfig

config = GoodmapConfig(
    APP_NAME="test",
    SECRET_KEY="test",
    DB=JsonDbConfig(DATA={}, TYPE="json"),
)


@pytest.mark.skip_coverage
def test_create_app():
    goodmap.create_app_from_config(config)


def test_create_app_from_config():
    with patch("platzky.platzky.create_app_from_config", MagicMock()) as mock_platzky_app_creation:
        with patch("goodmap.goodmap.extend_db_with_goodmap_queries", MagicMock()) as mock_extend_db:
            goodmap.create_app_from_config(config)
            mock_platzky_app_creation.assert_called_once_with(config)
            mock_extend_db.assert_called_once()


@mock.patch("goodmap.goodmap.create_app_from_config")
@mock.patch("goodmap.goodmap.GoodmapConfig.parse_yaml")
def test_create_app_delegation(mock_parse_yaml, mock_create_app_from_config):
    goodmap.create_app("dummy_path.yml")
    mock_parse_yaml.assert_called_once_with("dummy_path.yml")
    mock_create_app_from_config.assert_called_once_with(mock_parse_yaml.return_value)


def test_is_feature_enabled():
    # Test with feature flags set to True
    config_with_flag = GoodmapConfig(
        APP_NAME="test",
        SECRET_KEY="test",
        DB=JsonDbConfig(DATA={}, TYPE="json"),
        FEATURE_FLAGS={"flag": True, "other": False},
    )
    assert goodmap.is_feature_enabled(config_with_flag, "flag") is True
    assert goodmap.is_feature_enabled(config_with_flag, "other") is False

    # Test with feature flags set to empty dict
    config_no_flag = GoodmapConfig(
        APP_NAME="test",
        SECRET_KEY="test",
        DB=JsonDbConfig(DATA={}, TYPE="json"),
        FEATURE_FLAGS={},
    )
    assert goodmap.is_feature_enabled(config_no_flag, "flag") is False


@mock.patch("goodmap.goodmap.get_location_obligatory_fields")
def test_use_lazy_loading_branch(mock_get_location_obligatory_fields):
    config = GoodmapConfig(
        APP_NAME="test_lazy",
        SECRET_KEY="secret",
        DB=JsonDbConfig(DATA={"site_content": {}, "location_obligatory_fields": []}, TYPE="json"),
        FEATURE_FLAGS={"USE_LAZY_LOADING": True},
    )

    app = goodmap.create_app_from_config(config)
    mock_get_location_obligatory_fields.assert_called_once_with(app.db)

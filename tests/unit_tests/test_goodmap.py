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


def test_index_route_returns_location_schema():
    """Test that the index route (/) returns successfully with location_schema"""
    config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={
                "site_content": {"pages": []},
                "categories": {
                    "accessibility": ["wheelchair", "elevator"],
                    "amenities": ["wifi", "parking"],
                },
            },
            TYPE="json",
        ),
    )
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200

    # Verify location_schema is present in the response
    response_text = response.data.decode("utf-8")
    assert "LOCATION_SCHEMA" in response_text
    assert "obligatory_fields" in response_text
    assert "categories" in response_text
    assert "accessibility" in response_text
    assert "amenities" in response_text


def test_index_route_location_schema_with_lazy_loading():
    """Test that location_schema includes obligatory_fields when USE_LAZY_LOADING is enabled"""
    config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={
                "site_content": {"pages": []},
                "categories": {"test_category": ["option1"]},
                "location_obligatory_fields": [
                    ("name", "str"),
                    ("position", "list[float]"),
                    ("test_category", "list[str]"),
                ],
            },
            TYPE="json",
        ),
        FEATURE_FLAGS={"USE_LAZY_LOADING": True},
    )
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200

    # Verify location_schema includes obligatory_fields
    response_text = response.data.decode("utf-8")
    assert "LOCATION_SCHEMA" in response_text
    assert "name" in response_text
    assert "position" in response_text
    assert "test_category" in response_text

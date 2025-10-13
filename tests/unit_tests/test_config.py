import tempfile
from pathlib import Path

import pytest
from platzky.db.json_db import JsonDbConfig

from goodmap.config import GoodmapConfig


def test_goodmap_config_default_frontend_url():
    """Test that GoodmapConfig has the correct default frontend library URL."""
    config = GoodmapConfig(
        APP_NAME="test",
        SECRET_KEY="test",
        DB=JsonDbConfig(DATA={}, TYPE="json"),
    )
    assert (
        config.goodmap_frontend_lib_url == "https://cdn.jsdelivr.net/npm/@problematy/goodmap@0.4.2"
    )


def test_goodmap_config_custom_frontend_url():
    """Test that GoodmapConfig can be initialized with a custom frontend library URL."""
    custom_url = "https://example.com/custom-goodmap.js"
    config = GoodmapConfig(
        APP_NAME="test",
        SECRET_KEY="test",
        DB=JsonDbConfig(DATA={}, TYPE="json"),
        GOODMAP_FRONTEND_LIB_URL=custom_url,
    )
    assert config.goodmap_frontend_lib_url == custom_url


def test_goodmap_config_model_validate():
    """Test that model_validate returns correct GoodmapConfig type."""
    config_dict = {
        "APP_NAME": "test",
        "SECRET_KEY": "test",
        "DB": {"DATA": {}, "TYPE": "json"},
        "GOODMAP_FRONTEND_LIB_URL": "https://example.com/test.js",
    }
    config = GoodmapConfig.model_validate(config_dict)
    assert isinstance(config, GoodmapConfig)
    assert config.app_name == "test"
    assert config.goodmap_frontend_lib_url == "https://example.com/test.js"


def test_goodmap_config_parse_yaml_valid():
    """Test that parse_yaml successfully parses a valid YAML configuration file."""
    config_content = """
APP_NAME: test_app
SECRET_KEY: test_secret
DB:
  TYPE: json
  DATA: {}
GOODMAP_FRONTEND_LIB_URL: https://example.com/goodmap.js
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        config = GoodmapConfig.parse_yaml(temp_path)
        assert isinstance(config, GoodmapConfig)
        assert config.app_name == "test_app"
        assert config.secret_key == "test_secret"
        assert config.goodmap_frontend_lib_url == "https://example.com/goodmap.js"
    finally:
        Path(temp_path).unlink()


def test_goodmap_config_parse_yaml_with_default_url():
    """Test that parse_yaml uses default URL when not specified in YAML."""
    config_content = """
APP_NAME: test_app
SECRET_KEY: test_secret
DB:
  TYPE: json
  DATA: {}
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        config = GoodmapConfig.parse_yaml(temp_path)
        assert (
            config.goodmap_frontend_lib_url
            == "https://cdn.jsdelivr.net/npm/@problematy/goodmap@0.4.2"
        )
    finally:
        Path(temp_path).unlink()


def test_goodmap_config_parse_yaml_non_existing_file():
    """Test that parse_yaml raises SystemExit when file doesn't exist."""
    with pytest.raises(SystemExit) as exc_info:
        GoodmapConfig.parse_yaml("non_existing_config.yml")
    assert exc_info.value.code == 1


def test_goodmap_config_inherits_platzky_config():
    """Test that GoodmapConfig properly inherits PlatzkyConfig fields."""
    config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="secret123",
        DB=JsonDbConfig(DATA={}, TYPE="json"),
        FEATURE_FLAGS={"test_flag": True},
    )
    # Verify PlatzkyConfig fields are accessible (use lowercase field names)
    assert config.app_name == "test_app"
    assert config.secret_key == "secret123"
    assert config.feature_flags == {"test_flag": True}
    # Verify GoodmapConfig specific field
    assert (
        config.goodmap_frontend_lib_url == "https://cdn.jsdelivr.net/npm/@problematy/goodmap@0.4.2"
    )

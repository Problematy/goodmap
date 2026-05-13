import importlib.metadata
import os
import tempfile
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from platzky.db.json_db import JsonDbConfig

from goodmap import goodmap
from goodmap.config import GoodmapConfig
from goodmap.feature_flags import UseLazyLoading
from tests.unit_tests.conftest import make_flag_set

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
        mock_platzky_app_creation.return_value.is_enabled.return_value = False
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


@mock.patch("goodmap.goodmap.get_location_obligatory_fields")
def test_use_lazy_loading_branch(mock_get_location_obligatory_fields):
    config = GoodmapConfig(
        APP_NAME="test_lazy",
        SECRET_KEY="secret",
        DB=JsonDbConfig(DATA={"site_content": {}, "location_obligatory_fields": []}, TYPE="json"),
        FEATURE_FLAGS=make_flag_set(UseLazyLoading),
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
    # CSRF protection must be disabled in test environment to allow API testing
    # This is safe because tests run in isolation, not in production
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
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
        FEATURE_FLAGS=make_flag_set(UseLazyLoading),
    )
    app = goodmap.create_app_from_config(config)
    # CSRF protection must be disabled in test environment to allow API testing
    # This is safe because tests run in isolation, not in production
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200

    # Verify location_schema includes obligatory_fields
    response_text = response.data.decode("utf-8")
    assert "LOCATION_SCHEMA" in response_text
    assert "name" in response_text
    assert "position" in response_text
    assert "test_category" in response_text


def make_mock_entry_point(name: str, module_path: str):
    """Create a mock EntryPoint that loads a module from the given path.

    Creates a real module file so inspect.getfile resolves correctly.
    """
    os.makedirs(module_path, exist_ok=True)
    init_file = os.path.join(module_path, "__init__.py")
    if not os.path.exists(init_file):
        open(init_file, "w").close()

    spec = mock.MagicMock(spec=importlib.metadata.EntryPoint)
    spec.name = name

    mock_module = mock.MagicMock()
    mock_module.__file__ = init_file
    spec.load.return_value = mock_module
    return spec


def test_register_plugin_static_resources_with_static_dir():
    """Should return (blueprint, manifest) when plugin has a static directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "my_plugin")
        static_dir = os.path.join(plugin_dir, "static")
        os.makedirs(static_dir)

        ep = make_mock_entry_point("my_plugin", plugin_dir)

        with patch("goodmap.goodmap.inspect.getfile", lambda x: x.__file__):
            bp, entry = goodmap._register_plugin_static_resources(ep)

        assert bp is not None
        assert entry == {
            "scope": "my_plugin",
            "url": "/plugins/my_plugin/static/remoteEntry.js",
            "module": "./Button",
        }


def test_register_plugin_static_resources_no_static_dir():
    """Should return (None, None) when plugin has no static directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        ep = make_mock_entry_point("no_static_plugin", tmpdir)

        bp, entry = goodmap._register_plugin_static_resources(ep)

        assert bp is None
        assert entry is None


def test_register_plugin_static_resources_load_failure():
    """Should return (None, None) and log warning when plugin loading fails."""
    ep = mock.MagicMock(spec=importlib.metadata.EntryPoint)
    ep.name = "broken_plugin"
    ep.load.side_effect = ImportError("Module not found")

    with patch.object(goodmap.logger, "warning") as mock_warning:
        bp, entry = goodmap._register_plugin_static_resources(ep)

    assert bp is None
    assert entry is None
    mock_warning.assert_called_once_with(
        "Failed to serve static files for plugin '%s'", "broken_plugin"
    )




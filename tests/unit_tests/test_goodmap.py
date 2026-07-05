import importlib.metadata
import os
import sys
import tempfile
import types
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from platzky.db.json_db import JsonDbConfig

from goodmap import goodmap
from goodmap.config import GoodmapConfig
from goodmap.feature_flags import EnableAdminPanel, UseLazyLoading
from goodmap.plugin import (
    CAPABILITY_BASES,
    MapOverlayPluginBase,
    MarkerFieldDecoratorPluginBase,
    MarkerFieldPluginBase,
)
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
            mock_platzky_app_creation.assert_called_once_with(
                config,
                extra_plugin_bases=list(CAPABILITY_BASES),
                extra_plugins_entrypoints=["goodmap.plugins"],
            )
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


def test_frontend_lib_url_explicit_override_wins():
    """An explicit GOODMAP_FRONTEND_LIB_URL always takes priority over any bundle."""
    override_config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={
                "site_content": {"pages": []},
                "location_obligatory_fields": [],
                "categories": {},
            },
            TYPE="json",
        ),
        GOODMAP_FRONTEND_LIB_URL="https://example.com/custom.js",
    )
    app = goodmap.create_app_from_config(override_config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/map")

    assert 'src="https://example.com/custom.js"' in response.data.decode("utf-8")


def test_frontend_lib_url_uses_bundled_static_when_present():
    """With no override, serve the bundled file from the local static blueprint."""
    test_config = _make_test_app_config(
        extra_data={"location_obligatory_fields": [], "categories": {}}
    )
    app = goodmap.create_app_from_config(test_config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()
    response = client.get("/map")

    assert 'src="/static/frontend/index.min.js"' in response.data.decode("utf-8")


def test_index_route_returns_location_schema():
    """Test that the index route (/map) returns successfully with location_schema"""
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

    response = client.get("/map")
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

    response = client.get("/map")
    assert response.status_code == 200

    # Verify location_schema includes obligatory_fields
    response_text = response.data.decode("utf-8")
    assert "LOCATION_SCHEMA" in response_text
    assert "name" in response_text
    assert "position" in response_text
    assert "test_category" in response_text


def _plugin_ep(name: str, plugin_dir: str | None, base: type = MapOverlayPluginBase):
    """Create a mock EntryPoint whose load() returns a real ``base`` subclass.

    ``base`` is the goodmap capability base the plugin subclasses (its ``capability`` is
    read straight off the class into the manifest). The class's module file resolves to
    ``plugin_dir/__init__.py`` so the static-resource lookup points at ``plugin_dir/static``.
    Pass ``plugin_dir=None`` to make the module file unresolvable, exercising the
    static-registration failure path.
    """
    module = types.ModuleType(name)
    if plugin_dir is not None:
        os.makedirs(plugin_dir, exist_ok=True)
        init_file = os.path.join(plugin_dir, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, "w").close()
        module.__file__ = init_file
    else:
        module.__file__ = None
    sys.modules[name] = module

    cls = type("Plugin", (base,), {})
    cls.__module__ = name

    ep = mock.MagicMock(spec=importlib.metadata.EntryPoint)
    ep.name = name
    ep.load.return_value = cls
    return ep


def _patch_entry_points(groups: dict[str, list[Any]]):
    """Patch importlib.metadata.entry_points to return per-group entry points.

    Production resolves a distinct list per group; the global patch must mirror that so
    cross-group discovery (platzky + goodmap) doesn't see spurious duplicates.
    """

    def _fake_entry_points(*_args: Any, **kwargs: Any) -> list[Any]:
        group = kwargs.get("group")
        if group is None:
            return []
        return list(groups.get(group, []))

    return patch("importlib.metadata.entry_points", side_effect=_fake_entry_points)


def _plugin_config(name: str, plugin_config: dict[str, Any] | None = None) -> GoodmapConfig:
    return _make_test_app_config(
        extra_data={"plugins": {name: {"is_active": True, "config": plugin_config or {}}}}
    )


def test_plugin_with_static_dir():
    """Active overlay plugin with a static dir gets a blueprint + manifest entry incl. config."""
    config = _plugin_config("my_plugin", {"foo": "bar"})
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "my_plugin")
        os.makedirs(os.path.join(plugin_dir, "static"))

        ep = _plugin_ep("my_plugin", plugin_dir)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    assert "plugin_my_plugin" in app.blueprints
    assert app.config["PLUGIN_MANIFEST"] == [
        {
            "pluginName": "my_plugin",
            "url": "/plugins/my_plugin/static/remoteEntry.js",
            "module": "./MapOverlay",
            "capability": "overlay",
            "config": {"foo": "bar"},
        }
    ]


def test_field_plugin_is_manifested_with_field_capability():
    """A MarkerFieldPluginBase plugin is manifested with ``capability: "field"``."""
    config = _plugin_config("promo", {"color": "#0f0"})
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "promo")
        os.makedirs(os.path.join(plugin_dir, "static"))

        ep = _plugin_ep("promo", plugin_dir, base=MarkerFieldPluginBase)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    assert app.config["PLUGIN_MANIFEST"] == [
        {
            "pluginName": "promo",
            "url": "/plugins/promo/static/remoteEntry.js",
            "module": "./MarkerField",
            "capability": "field",
            "config": {"color": "#0f0"},
        }
    ]


def test_field_decorator_plugin_is_manifested_with_decorator_capability():
    """A decorator plugin is manifested with ``capability: "field-decorator"``."""
    config = _plugin_config("tracker", {"decorates": "hyperlink"})
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "tracker")
        os.makedirs(os.path.join(plugin_dir, "static"))

        ep = _plugin_ep("tracker", plugin_dir, base=MarkerFieldDecoratorPluginBase)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    assert app.config["PLUGIN_MANIFEST"] == [
        {
            "pluginName": "tracker",
            "url": "/plugins/tracker/static/remoteEntry.js",
            "module": "./MarkerFieldDecorator",
            "capability": "field-decorator",
            "config": {"decorates": "hyperlink"},
        }
    ]


def test_plugin_with_multiple_frontend_capabilities_gets_one_entry_per_capability():
    """A plugin subclassing two capability bases is manifested once per capability."""

    class _OverlayAndField(MapOverlayPluginBase, MarkerFieldPluginBase):
        pass

    config = _plugin_config("silly", {"gif": "cat.gif"})
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "silly")
        os.makedirs(os.path.join(plugin_dir, "static"))

        ep = _plugin_ep("silly", plugin_dir, base=_OverlayAndField)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    by_capability = {e["capability"]: e for e in app.config["PLUGIN_MANIFEST"]}
    assert set(by_capability) == {"overlay", "field"}
    assert by_capability["overlay"]["module"] == "./MapOverlay"
    assert by_capability["field"]["module"] == "./MarkerField"
    # Same plugin, same bundle URL, same config across both entries.
    assert all(
        e["pluginName"] == "silly"
        and e["url"] == "/plugins/silly/static/remoteEntry.js"
        and e["config"] == {"gif": "cat.gif"}
        for e in app.config["PLUGIN_MANIFEST"]
    )


def test_plugin_inactive_is_not_served():
    """A plugin that is installed but not active in config gets no frontend manifest entry."""
    config = _make_test_app_config()  # no plugins configured -> inactive
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "off_plugin")
        os.makedirs(os.path.join(plugin_dir, "static"))

        ep = _plugin_ep("off_plugin", plugin_dir)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    assert "plugin_off_plugin" not in app.blueprints
    assert app.config["PLUGIN_MANIFEST"] == []


def test_plugin_without_static_dir():
    """Active overlay plugin without a static dir gets no blueprint/manifest entry."""
    config = _plugin_config("no_static_plugin")
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "no_static_plugin")
        ep = _plugin_ep("no_static_plugin", plugin_dir)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    assert "plugin_no_static_plugin" not in app.blueprints
    assert app.config["PLUGIN_MANIFEST"] == []


def test_plugin_static_registration_failure_is_skipped():
    """An active plugin whose static resources can't be resolved is skipped with a warning."""
    config = _plugin_config("weird_plugin")
    ep = _plugin_ep("weird_plugin", plugin_dir=None)  # module file unresolvable

    with _patch_entry_points({"goodmap.plugins": [ep]}):
        with patch.object(goodmap.logger, "warning") as mock_warning:
            app = goodmap.create_app_from_config(config)

    assert "plugin_weird_plugin" not in app.blueprints
    assert app.config["PLUGIN_MANIFEST"] == []
    mock_warning.assert_any_call("Failed to serve static files for plugin '%s'", "weird_plugin")


def _make_test_app_config(feature_flags: Any = None, extra_data: Any = None) -> GoodmapConfig:
    data: dict[str, Any] = {
        "site_content": {"pages": []},
        "location_obligatory_fields": [],
    }
    if extra_data:
        data.update(extra_data)
    return GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(DATA=data, TYPE="json"),
        FEATURE_FLAGS=feature_flags,
    )


def test_admin_route_disabled():
    """Should redirect to / when admin panel feature flag is disabled."""
    config = _make_test_app_config()
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/goodmap-admin")

    assert response.status_code == 302
    assert response.location == "/"


def test_admin_route_no_user():
    """Should redirect to /admin when user is not logged in."""
    config = _make_test_app_config(feature_flags=make_flag_set(EnableAdminPanel))
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/goodmap-admin")

    assert response.status_code == 302
    assert response.location == "/admin"


def test_admin_route_logged_in():
    """Should render admin template when user is logged in."""
    config = _make_test_app_config(feature_flags=make_flag_set(EnableAdminPanel))
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    with client.session_transaction() as sess:
        sess["user"] = {"username": "Test User"}

    response = client.get("/goodmap-admin")

    assert response.status_code == 200
    response_text = response.data.decode("utf-8")
    assert "Test User" in response_text


def test_field_renderer_shortcodes_collected_from_content_transformer_plugins() -> None:
    """Shortcodes from all ContentTransformerPluginBase plugins are passed to core_pages."""
    from typing import ClassVar

    from platzky.content_types import ALL_CONTENT_TYPES
    from platzky.plugin.content_transformer import ContentTransformerPluginBase
    from platzky.shortcodes import Shortcode, ShortcodeAttrs

    class _FieldSC(Shortcode):
        name = "testfieldsc"
        description = "Field-capable shortcode"

        def render(self, attrs: ShortcodeAttrs, content: str) -> str:
            return content

    class _PostSC(Shortcode):
        name = "testpostsc"
        description = "Post-only shortcode"

        def render(self, attrs: ShortcodeAttrs, content: str) -> str:
            return content

    class _PluginA(ContentTransformerPluginBase):
        shortcodes: ClassVar[dict[str, Shortcode]] = {"testfieldsc": _FieldSC()}

    class _PluginB(ContentTransformerPluginBase):
        shortcodes: ClassVar[dict[str, Shortcode]] = {"testpostsc": _PostSC()}

    config = _make_test_app_config(
        extra_data={
            "plugins": {
                "field_plugin": {
                    "is_active": True,
                    "config": {},
                    "allowed_content_types": list(ALL_CONTENT_TYPES),
                    "allowed_topics": ["general", "content", "security"],
                },
                "post_plugin": {
                    "is_active": True,
                    "config": {},
                    "allowed_content_types": list(ALL_CONTENT_TYPES),
                    "allowed_topics": ["general", "content", "security"],
                },
            }
        }
    )

    captured: dict[str, Any] = {}
    orig_core_pages = goodmap.core_pages

    def _spy_core_pages(*args: Any, **kwargs: Any) -> Any:
        captured["shortcodes"] = kwargs.get("shortcodes", {})
        return orig_core_pages(*args, **kwargs)

    field_ep = mock.MagicMock()
    field_ep.name = "field_plugin"
    field_ep.load.return_value = _PluginA

    post_ep = mock.MagicMock()
    post_ep.name = "post_plugin"
    post_ep.load.return_value = _PluginB

    with mock.patch("goodmap.goodmap.core_pages", side_effect=_spy_core_pages):
        with _patch_entry_points({"platzky.plugins": [field_ep, post_ep]}):
            goodmap.create_app_from_config(config)

    assert "testfieldsc" in captured["shortcodes"]
    assert "testpostsc" in captured["shortcodes"]


def test_plugin_blueprint_sets_cors_header():
    """Should set Access-Control-Allow-Origin on plugin blueprint responses."""
    config = _plugin_config("cors_plugin")
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "cors_plugin")
        static_dir = os.path.join(plugin_dir, "static")
        os.makedirs(static_dir)

        # Create a test file in the static dir
        open(os.path.join(static_dir, "test.js"), "w").close()

        ep = _plugin_ep("cors_plugin", plugin_dir)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

        app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
        client = app.test_client()

        response = client.get("/plugins/cors_plugin/static/test.js")

        assert response.status_code == 200
        assert response.headers.get("Access-Control-Allow-Origin") == "*"

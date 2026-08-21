import importlib.metadata
import io
import os
import sys
import tempfile
import types
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from platzky.config import AttachmentConfig
from platzky.db.json_db import JsonDbConfig

from goodmap import goodmap
from goodmap.config import GoodmapConfig
from goodmap.feature_flags import EnableAdminPanel
from goodmap.plugin import (
    CAPABILITY_BASES,
    MapOverlayPluginBase,
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
        with (
            patch("goodmap.goodmap.extend_db_with_goodmap_queries", MagicMock()) as mock_extend_db,
            patch("goodmap.goodmap.get_location_obligatory_fields", return_value=[]),
            patch("goodmap.goodmap.get_category_data") as mock_get_category_data,
            patch("goodmap.goodmap.get_marker_styles") as mock_get_marker_styles,
        ):
            mock_get_category_data.return_value.return_value = {"categories": {}}
            mock_get_marker_styles.return_value.return_value = {}
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
def test_location_model_is_always_built_from_the_data_source(mock_get_location_obligatory_fields):
    """Building the location model from location_obligatory_fields/categories is
    unconditional - there's no flag that skips it (see feature_flags.py)."""
    config = GoodmapConfig(
        APP_NAME="test_lazy",
        SECRET_KEY="secret",
        DB=JsonDbConfig(DATA={"site_content": {}, "location_obligatory_fields": []}, TYPE="json"),
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


def test_map_route_marker_styles():
    """The frontend picks pin icon/color per marker_styles.config's iconField/colorField
    at runtime from window.MARKER_STYLES - a deployment-specific lookup table that lives
    in the database (like categories/visible_data), not hardcoded in the frontend build.
    Deployments that don't configure it get an empty object instead, so the frontend
    falls back to Leaflet's default marker - no behavior change."""
    configured_config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={
                "site_content": {"pages": []},
                "categories": {"type_of_place": ["parcel_locker", "container"]},
                "marker_styles": {
                    "icon_field": "type_of_place",
                    "icons": {
                        "parcel_locker": "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets/fill/package-fill.svg"
                    },
                    "colors": {},
                },
            },
            TYPE="json",
        ),
    )
    configured_app = goodmap.create_app_from_config(configured_config)
    configured_app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR

    response = configured_app.test_client().get("/map")
    assert response.status_code == 200

    response_text = response.data.decode("utf-8")
    assert "MARKER_STYLES" in response_text
    assert "icon_field" in response_text
    assert "parcel_locker" in response_text

    unconfigured_app = goodmap.create_app_from_config(_minimal_config())
    unconfigured_app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR

    response = unconfigured_app.test_client().get("/map")
    assert response.status_code == 200
    assert "window.MARKER_STYLES={};" in response.data.decode("utf-8")


def test_map_route_marker_styles_stay_in_step_with_the_api():
    """window.MARKER_STYLES comes from the startup-time config, not a fresh read per
    request. The field /api/locations reads marker.icon from is fixed at startup, so a
    /map that served newer lookup tables would key them on values the API isn't
    sending."""
    data = {
        "site_content": {"pages": []},
        "location_obligatory_fields": [["type_of_place", "str"]],
        "marker_styles": {
            "icon_field": "type_of_place",
            "icons": {"parcel_locker": "https://cdn.example.com/package.svg"},
            "colors": {},
        },
    }
    app = goodmap.create_app_from_config(
        GoodmapConfig(
            APP_NAME="test_app",
            SECRET_KEY="test_secret",
            USE_WWW=False,
            BLOG_PREFIX="/blog",
            DB=JsonDbConfig(DATA=data, TYPE="json"),
        )
    )
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR

    with mock.patch.object(app.db, "get_marker_styles") as fresh_read:
        response_text = app.test_client().get("/map").data.decode("utf-8")

    fresh_read.assert_not_called()
    assert "parcel_locker" in response_text


def test_map_route_includes_photo_constraints():
    """The frontend sources photo upload limits (max size, allowed types) live from
    the backend's AttachmentConfig rather than hardcoding its own copy - this test
    guards the `photo` key in /api/location-schema that makes that possible.
    """
    config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={"site_content": {"pages": []}, "categories": {}},
            TYPE="json",
        ),
    )
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/api/location-schema")
    assert response.status_code == 200

    assert response.json is not None
    photo = response.json["photo"]
    assert photo["max_size_bytes"] == 5242880
    assert photo["allowed_mime_types"] == ["image/jpeg"]
    assert photo["allowed_extensions"] == ["jpeg", "jpg"]


def _minimal_config() -> GoodmapConfig:
    return GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={"site_content": {"pages": []}, "categories": {}},
            TYPE="json",
        ),
    )


def _config_with_attachment(attachment: AttachmentConfig) -> GoodmapConfig:
    return GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={"site_content": {"pages": []}, "categories": {}},
            TYPE="json",
        ),
        ATTACHMENT=attachment,
    )


def test_max_content_length_leaves_room_for_an_attachment_at_the_configured_limit():
    """The request size cap must exceed attachment.max_size, or Flask would reject an
    otherwise-valid photo with 413 before it ever reaches attachment validation.
    """
    app = goodmap.create_app_from_config(_minimal_config())

    max_content_length = app.config["MAX_CONTENT_LENGTH"]
    assert max_content_length is not None, "request size cap must actually be applied"
    assert max_content_length > 5 * 1024 * 1024


def test_max_content_length_tracks_a_raised_attachment_limit():
    """Raising ATTACHMENT.max_size must raise the request cap with it."""
    app = goodmap.create_app_from_config(
        _config_with_attachment(
            AttachmentConfig(
                allowed_mime_types=frozenset({"image/jpeg"}),
                allowed_extensions=frozenset({"jpg", "jpeg"}),
                max_size=8 * 1024 * 1024,
            )
        )
    )

    assert app.config["MAX_CONTENT_LENGTH"] > 8 * 1024 * 1024


def test_max_content_length_rejects_bodies_past_the_cap():
    """Oversized requests are still dropped rather than buffered into memory."""
    app = goodmap.create_app_from_config(_minimal_config())
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    oversized = b"x" * (app.config["MAX_CONTENT_LENGTH"] + 1)
    response = client.post(
        "/api/suggest-new-point",
        data={"position": "[50, 50]", "photo": (io.BytesIO(oversized), "photo.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 413


def test_map_route_overrides_photo_constraints():
    """A deployment can override the default JPEG-only 5MiB photo constraints via
    ATTACHMENT: in its YAML config - goodmap must read config.attachment (platzky's
    own config field) rather than hardcoding its own AttachmentConfig.
    """
    config = GoodmapConfig(
        APP_NAME="test_app",
        SECRET_KEY="test_secret",
        USE_WWW=False,
        BLOG_PREFIX="/blog",
        DB=JsonDbConfig(
            DATA={"site_content": {"pages": []}, "categories": {}},
            TYPE="json",
        ),
        ATTACHMENT=AttachmentConfig(
            allowed_mime_types=frozenset({"image/jpeg", "image/png"}),
            allowed_extensions=frozenset({"jpg", "jpeg", "png"}),
            max_size=8 * 1024 * 1024,
        ),
    )
    app = goodmap.create_app_from_config(config)
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/api/location-schema")
    assert response.status_code == 200

    assert response.json is not None
    photo = response.json["photo"]
    assert photo["max_size_bytes"] == 8388608
    assert photo["allowed_mime_types"] == ["image/jpeg", "image/png"]
    assert photo["allowed_extensions"] == ["jpeg", "jpg", "png"]


def test_location_schema_endpoint_includes_obligatory_fields():
    """The schema includes this deployment's obligatory_fields - unconditional,
    there's no flag that skips building the location model from them."""
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
    )
    app = goodmap.create_app_from_config(config)
    # CSRF protection must be disabled in test environment to allow API testing
    # This is safe because tests run in isolation, not in production
    app.config["WTF_CSRF_ENABLED"] = False  # NOSONAR
    client = app.test_client()

    response = client.get("/api/location-schema")
    assert response.status_code == 200

    schema = response.json
    assert schema is not None
    assert [f[0] for f in schema["obligatory_fields"]] == [
        "name",
        "position",
        "test_category",
    ]
    # position is client-supplied, so it must be offered as a field; uuid is not
    assert "position" in schema["fields"]
    assert "uuid" not in schema["fields"]


def _plugin_ep(name: str, plugin_dir: str | None, base: type = MapOverlayPluginBase):
    """Create a mock EntryPoint whose load() returns a real ``base`` subclass.

    ``base`` is the goodmap capability base the plugin subclasses (its manifest capability
    is derived from the base class name). The class's module file resolves to
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
            "capability": "MapOverlay",
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
            "capability": "MarkerField",
            "config": {"color": "#0f0"},
        }
    ]


def test_field_plugin_config_is_passed_through_to_the_manifest():
    """A field plugin is manifested as ``"MarkerField"``; its ``config`` (``field``/``order``,
    which the frontend uses to place it in the fold) is passed through untouched."""
    config = _plugin_config("tracker", {"field": "hyperlink", "order": 1})
    with tempfile.TemporaryDirectory() as tmpdir:
        plugin_dir = os.path.join(tmpdir, "tracker")
        os.makedirs(os.path.join(plugin_dir, "static"))

        ep = _plugin_ep("tracker", plugin_dir, base=MarkerFieldPluginBase)

        with _patch_entry_points({"goodmap.plugins": [ep]}):
            app = goodmap.create_app_from_config(config)

    assert app.config["PLUGIN_MANIFEST"] == [
        {
            "pluginName": "tracker",
            "url": "/plugins/tracker/static/remoteEntry.js",
            "module": "./MarkerField",
            "capability": "MarkerField",
            "config": {"field": "hyperlink", "order": 1},
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
    assert set(by_capability) == {"MapOverlay", "MarkerField"}
    assert by_capability["MapOverlay"]["module"] == "./MapOverlay"
    assert by_capability["MarkerField"]["module"] == "./MarkerField"
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


def test_csrf_protect_is_initialized_exactly_once():
    """platzky already initializes CSRFProtect; goodmap must not add a second hook."""
    config = _make_test_app_config(extra_data={"categories": {}})
    app = goodmap.create_app_from_config(config)
    hooks = [f.__name__ for f in app.before_request_funcs.get(None, [])]
    assert hooks.count("csrf_protect") == 1


def test_csrf_failure_returns_json_error():
    """A rejected write gets the API's JSON error shape, not an HTML error page."""
    config = _make_test_app_config(extra_data={"categories": {}, "data": []})
    app = goodmap.create_app_from_config(config)
    client = app.test_client()

    response = client.post("/api/report-location", json={"id": "x", "description": "y"})

    assert response.status_code == 400
    assert response.content_type.startswith("application/json")
    assert response.json == {"message": "The CSRF token is missing."}


def test_csrf_enforces_referer_on_https():
    """WTF_CSRF_SSL_STRICT is left on: https requires a same-origin Referer, on top
    of the token/session check, as defense-in-depth against a forged cross-origin
    request. A real browser sends a matching Referer automatically for a same-origin
    request, so this only rejects scripted callers that omit it or spoof it.
    """
    import re

    config = _make_test_app_config(extra_data={"categories": {}, "data": []})
    app = goodmap.create_app_from_config(config)
    client = app.test_client()

    page = client.get("/map", base_url="https://localhost")
    token_match = re.search(r'name="csrf-token" content="([^"]+)"', page.data.decode("utf-8"))
    assert token_match is not None
    token = token_match.group(1)
    payload = {"id": "x", "description": "y"}

    # Same-origin Referer, as a real browser sends by default: past the CSRF layer.
    # The handler may still reject the payload, but not with a CSRF message.
    response = client.post(
        "/api/report-location",
        json=payload,
        headers={"X-CSRFToken": token, "Referer": "https://localhost/map"},
        base_url="https://localhost",
    )
    assert "CSRF" not in response.get_data(as_text=True)

    # No Referer at all: rejected.
    response = client.post(
        "/api/report-location",
        json=payload,
        headers={"X-CSRFToken": token},
        base_url="https://localhost",
    )
    assert response.status_code == 400
    assert response.json == {"message": "The referrer header is missing."}

    # Cross-origin Referer: rejected. This is the actual attack the check defends
    # against - a request that carries a valid token but did not originate here.
    response = client.post(
        "/api/report-location",
        json=payload,
        headers={"X-CSRFToken": token, "Referer": "https://evil.example/"},
        base_url="https://localhost",
    )
    assert response.status_code == 400
    assert response.json == {"message": "The referrer does not match the host."}


def test_csrf_token_is_session_scoped():
    """The token alone is not enough - it must be paired with the session it was minted in."""
    import re

    config = _make_test_app_config(extra_data={"categories": {}, "data": []})
    app = goodmap.create_app_from_config(config)
    assert app.config["WTF_CSRF_TIME_LIMIT"] is None

    victim = app.test_client()
    page = victim.get("/map")
    token_match = re.search(r'name="csrf-token" content="([^"]+)"', page.data.decode("utf-8"))
    assert token_match is not None
    token = token_match.group(1)

    attacker = app.test_client()
    response = attacker.post(
        "/api/report-location",
        json={"id": "x", "description": "y"},
        headers={"X-CSRFToken": token},
    )
    assert response.status_code == 400
    assert response.json == {"message": "The CSRF session token is missing."}


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

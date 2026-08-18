"""Goodmap engine with location management and admin interface."""

import importlib.metadata
import inspect
import logging
import os
from typing import Any

from flask import Blueprint, jsonify, redirect, render_template, session
from flask_babel import gettext
from flask_wtf.csrf import CSRFError, generate_csrf
from platzky import platzky
from platzky.config import languages_dict
from platzky.models import CmsModule
from platzky.plugin.content_transformer import ContentTransformerPluginBase
from platzky.shortcodes import Shortcode
from pydantic import BaseModel

from goodmap.admin_api import admin_pages
from goodmap.config import GoodmapConfig
from goodmap.core_api import core_pages
from goodmap.data_models.location import create_location_model
from goodmap.db import (
    extend_db_with_goodmap_queries,
    get_location_obligatory_fields,
)
from goodmap.feature_flags import EnableAdminPanel, UseLazyLoading
from goodmap.plugin import CAPABILITY_BASES, GoodmapPluginBase

logger = logging.getLogger(__name__)

_PLUGIN_ENTRY_POINT_GROUP = "goodmap.plugins"

# Room above the attachment limit for a suggestion's text fields and multipart framing.
MULTIPART_OVERHEAD_ALLOWANCE = 100 * 1024


def _frontend_capability_bases(plugin_class: Any) -> list[type[GoodmapPluginBase]]:
    """The goodmap frontend capability bases a plugin subclasses (may be several).

    Derived by class-based recognition, the same way platzky matches plugins against its
    capability bases. A plugin can provide multiple frontend capabilities (e.g. an overlay
    and a marker field) by subclassing more than one base.
    """
    if not isinstance(plugin_class, type):
        return []
    return [base for base in CAPABILITY_BASES if issubclass(plugin_class, base)]


def _register_plugin_static_resources(
    ep: importlib.metadata.EntryPoint,
) -> tuple[Blueprint | None, list[dict[str, Any]]]:
    """Load a plugin's static resources and return its blueprint and manifest entries.

    Loads the plugin module, checks for a 'static' directory, and if found creates a Flask
    blueprint plus one manifest entry per frontend capability the plugin provides. Each
    capability points at its own Module Federation ``module``, all served from the plugin's
    single ``remoteEntry.js``.

    Args:
        ep: The entry point for the plugin.

    Returns:
        A tuple of (blueprint, manifest_entries). The blueprint is None and the list empty
        if the plugin has no static directory, no frontend capability, or loading fails.
    """
    try:
        plugin_class = ep.load()
        mod_path = os.path.dirname(os.path.realpath(inspect.getfile(plugin_class)))
        static_dir = os.path.join(mod_path, "static")
        if not os.path.isdir(static_dir):
            return None, []

        # One manifest entry per capability the plugin provides. "capability" tells the
        # frontend which handler mounts the component (overlay via MapOverlays, field via
        # FieldRenderer, …) and "module" is that capability's Module Federation key.
        bases = _frontend_capability_bases(plugin_class)
        if not bases:
            return None, []

        bp = Blueprint(
            f"plugin_{ep.name}",
            __name__,
            url_prefix=f"/plugins/{ep.name}",
            static_folder=static_dir,
            static_url_path="/static",
        )

        @bp.after_request
        def _add_cors(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            return response

        entries = []
        for base in bases:
            # The capability token and its Module Federation key are derived from the base
            # class name (MapOverlayPluginBase -> "MapOverlay" / "./MapOverlay"), so the
            # class is the single source of truth — no separate identifier to keep in sync.
            capability = base.__name__.removesuffix("PluginBase")
            entries.append(
                {
                    "pluginName": ep.name,
                    "url": f"/plugins/{ep.name}/static/remoteEntry.js",
                    "module": f"./{capability}",
                    "capability": capability,
                }
            )
        return bp, entries
    except Exception:
        logger.warning("Failed to serve static files for plugin '%s'", ep.name)
        return None, []


def _setup_location_model(
    db: Any,
) -> tuple[list[Any], dict[str, Any], type[BaseModel], Any]:
    """Configure location model and db with lazy-loading and categories support.

    Args:
        db: The database instance to extend with location queries.

    Returns:
        Tuple of (obligatory_fields, categories, location_model, db).
    """
    obligatory_fields = get_location_obligatory_fields(db)
    location_model = create_location_model(obligatory_fields, {})
    extended_db = extend_db_with_goodmap_queries(db, location_model)

    try:
        category_data = extended_db.get_category_data()
        categories = category_data.get("categories", {})
    except (KeyError, AttributeError):
        categories = {}

    if categories:
        location_model = create_location_model(obligatory_fields, categories)
        extended_db = extend_db_with_goodmap_queries(extended_db, location_model)

    return obligatory_fields, categories, location_model, extended_db


def create_app(config_path: str) -> platzky.Engine:
    """Create Goodmap application from YAML configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        platzky.Engine: Configured Flask application
    """
    config = GoodmapConfig.parse_yaml(config_path)
    return create_app_from_config(config)


def create_app_from_config(config: GoodmapConfig) -> platzky.Engine:
    """Create and configure Goodmap application from config object.

    Sets up location models, database queries, CSRF protection, API blueprints,
    and admin interface based on the provided configuration.

    Args:
        config: Goodmap configuration object

    Returns:
        platzky.Engine: Fully configured Flask application with Goodmap features
    """
    directory = os.path.dirname(os.path.realpath(__file__))

    locale_dir = os.path.join(directory, "locale")
    config.translation_directories.append(locale_dir)
    # Register goodmap's own plugin ecosystem with platzky: MapOverlayPluginBase is a
    # host-defined capability, and goodmap plugins are discovered from the
    # "goodmap.plugins" entry-point group. This makes them config-gated (is_active)
    # through platzky's normal plugin loader, alongside platzky's own plugins.
    app = platzky.create_app_from_config(
        config,
        extra_plugin_bases=list(CAPABILITY_BASES),
        extra_plugins_entrypoints=[_PLUGIN_ENTRY_POINT_GROUP],
    )

    frontend_static_dir = os.path.join(directory, "static", "frontend")
    app.register_blueprint(
        Blueprint(
            "goodmap_frontend",
            __name__,
            static_folder=frontend_static_dir,
            static_url_path="/static/frontend",
        )
    )

    # SECURITY: cap request bodies so oversized ones are dropped before being buffered
    # into memory. Sized to the largest legitimate suggestion - an attachment at the
    # configured limit, plus headroom for the form fields and multipart overhead -
    # since anything above that could never pass validation anyway.
    # Flask seeds MAX_CONTENT_LENGTH with None, so this checks the value, not the key.
    if app.config.get("MAX_CONTENT_LENGTH") is None:
        app.config["MAX_CONTENT_LENGTH"] = config.attachment.max_size + MULTIPART_OVERHEAD_ALLOWANCE

    if app.is_enabled(UseLazyLoading):
        location_obligatory_fields, _, location_model, app.db = _setup_location_model(app.db)
    else:
        location_obligatory_fields = []
        location_model = create_location_model([], {})
        app.db = extend_db_with_goodmap_queries(app.db, location_model)

    app.extensions["goodmap"] = {"location_obligatory_fields": location_obligatory_fields}

    try:
        plugins_data = app.db.get_plugins_data()
    except Exception:
        logger.warning(
            "Could not read plugin config data; frontend plugins get empty config",
            exc_info=True,
        )
        plugins_data = {}

    plugin_manifest = []
    for ep in importlib.metadata.entry_points(group=_PLUGIN_ENTRY_POINT_GROUP):
        plugin_cfg = plugins_data.get(ep.name)
        # Only serve the frontend for plugins that are explicitly enabled in config.
        # platzky's loader has already instantiated the active ones (gated identically),
        # so the manifest stays in lockstep with the loaded backend plugins.
        if plugin_cfg is None or not plugin_cfg.is_active:
            continue
        bp, entries = _register_plugin_static_resources(ep)
        if bp is not None and entries:
            app.register_blueprint(bp)
            for entry in entries:
                entry["config"] = plugin_cfg.config
                plugin_manifest.append(entry)

    app.config["PLUGIN_MANIFEST"] = plugin_manifest

    # CSRF protection itself is initialized by platzky (create_app_from_config runs
    # CSRFProtect on the engine); initializing it here again would register a second
    # before_request hook and break any future exempt() registered on one instance only.
    #
    # The token is bound to the session, which is the actual protection. The extra
    # referrer check flask-wtf adds on https would reject scripted API callers that
    # send a valid token but no Referer header, so it is off.
    app.config["WTF_CSRF_SSL_STRICT"] = False
    # The map page is typically left open well past the default 3600s, and the frontend
    # never refreshes the meta-tag token - so scope the token to the session instead of
    # rejecting submissions from any tab older than an hour.
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        """Return CSRF failures in the API's JSON error shape instead of an HTML page."""
        return jsonify({"message": error.description}), 400

    photo_attachment_config = config.attachment

    shortcodes: dict[str, Shortcode] = {}
    for plugin in app.loaded_plugins:
        if isinstance(plugin, ContentTransformerPluginBase):
            for name, sc in plugin.shortcodes.items():
                if name in shortcodes:
                    logger.warning(
                        "Shortcode '%s' from plugin '%s' conflicts with "
                        "an already-registered shortcode; skipping",
                        name,
                        type(plugin).__name__,
                    )
                else:
                    shortcodes[name] = sc

    cp = core_pages(
        app.db,
        languages_dict(config.languages),
        app.notify,
        generate_csrf,
        location_model,
        photo_attachment_config=photo_attachment_config,
        feature_flags=config.feature_flags,
        shortcodes=shortcodes,
    )
    app.register_blueprint(cp)

    goodmap = Blueprint("goodmap", __name__, url_prefix="/", template_folder="templates")

    @goodmap.route("/map")
    def index():
        """Render main map interface with location schema.

        Registered at /map rather than / because platzky (>=2.0.0a8) reserves
        the root path for its own homepage dispatch (see
        db.get_home_page_path()). Deployments set site_content.home_page_path
        to "/map" so visiting / still renders this view, with no redirect.

        Prepares and passes location schema including obligatory fields and
        categories to the frontend for dynamic form generation.

        Returns:
            Rendered map.html template with feature flags and location schema
        """
        # Prepare location schema for frontend dynamic forms
        # Include full schema from Pydantic model for better type information
        category_data = app.db.get_category_data()  # type: ignore[attr-defined]
        categories = category_data.get("categories", {})

        # Get full JSON schema from Pydantic model
        model_json_schema = location_model.model_json_schema()
        properties = model_json_schema.get("properties", {})

        # Filter out uuid and position from properties for frontend form
        form_fields = {
            name: spec for name, spec in properties.items() if name not in ("uuid", "position")
        }

        issue_options_raw = app.db.get_issue_options()  # type: ignore[attr-defined]
        reported_issue_types = [{"value": t, "label": gettext(t)} for t in issue_options_raw]

        location_schema = {  # TODO remove backward compatibility - deprecation
            "obligatory_fields": app.extensions["goodmap"][
                "location_obligatory_fields"
            ],  # Backward compatibility
            "categories": categories,  # Backward compatibility
            "fields": form_fields,
            "reported_issue_types": reported_issue_types,
            "photo": {
                "allowed_extensions": sorted(photo_attachment_config.allowed_extensions or []),
                "allowed_mime_types": sorted(photo_attachment_config.allowed_mime_types or []),
                "max_size_bytes": photo_attachment_config.max_size,
            },
        }

        return render_template(
            "map.html",
            feature_flags=config.feature_flags,
            goodmap_frontend_lib_url=config.goodmap_frontend_lib_url,
            location_schema=location_schema,
            plugin_manifest=plugin_manifest,
        )

    @goodmap.route("/goodmap-admin")
    def admin():
        """Render admin interface for managing map data.

        Requires user to be logged in (redirects to /admin if not).
        Provides admin panel for managing locations, suggestions, and reports.
        Only available when ENABLE_ADMIN_PANEL feature flag is enabled.

        Returns:
            Rendered goodmap-admin.html template or redirect to login
        """
        if not app.is_enabled(EnableAdminPanel):
            return redirect("/")

        user = session.get("user", None)
        if not user:
            return redirect("/admin")

        # TODO: This should be replaced with a proper user authentication check,
        #       cms_modules should be passed from the app
        return render_template(
            "goodmap-admin.html",
            feature_flags=config.feature_flags,
            goodmap_frontend_lib_url=config.goodmap_frontend_lib_url,
            user=user,
            cms_modules=app.cms_modules,
        )

    app.register_blueprint(goodmap)

    if app.is_enabled(EnableAdminPanel):
        admin_bp = admin_pages(app.db, location_model)
        app.register_blueprint(admin_bp)

        goodmap_cms_modules = CmsModule.model_validate(
            {
                "name": "Map admin panel",
                "description": "Admin panel for managing map data",
                "slug": "goodmap-admin",
                "template": "goodmap-admin.html",
            }
        )
        app.add_cms_module(goodmap_cms_modules)

    return app

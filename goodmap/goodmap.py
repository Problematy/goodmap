"""Goodmap engine with location management and admin interface."""

import importlib.metadata
import inspect
import logging
import os
from typing import Any

from flask import Blueprint, redirect, render_template, session
from flask_babel import gettext
from flask_wtf.csrf import CSRFProtect, generate_csrf
from platzky import platzky
from platzky.attachment import create_attachment_class
from platzky.config import AttachmentConfig, languages_dict
from platzky.models import CmsModule
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

logger = logging.getLogger(__name__)

_PLUGIN_ENTRY_POINT_GROUP = "platzky.plugins"


def _register_plugin_static_resources(
    ep: importlib.metadata.EntryPoint,
) -> tuple[Blueprint | None, dict[str, Any] | None]:
    """Load a plugin's static resources and return its blueprint and manifest entry.

    Loads the plugin module, checks for a 'static' directory, and if found
    creates a Flask blueprint and a manifest entry for the frontend.

    Args:
        ep: The entry point for the plugin.

    Returns:
        A tuple of (blueprint, manifest_entry). Both are None if the plugin
        has no static directory or loading fails.
    """
    try:
        mod_path = os.path.dirname(os.path.realpath(inspect.getfile(ep.load())))
        static_dir = os.path.join(mod_path, "static")
        if not os.path.isdir(static_dir):
            return None, None

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

        manifest_entry = {
            "scope": ep.name,
            "url": f"/plugins/{ep.name}/static/remoteEntry.js",
            "module": "./Button",
        }
        return bp, manifest_entry
    except Exception:
        logger.warning("Failed to serve static files for plugin '%s'", ep.name)
        return None, None


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
    app = platzky.create_app_from_config(config)

    # SECURITY: Set maximum request body size to 100KB (prevents memory exhaustion)
    # This protects against large file uploads and JSON payloads
    # Based on calculation: ~6.5KB max legitimate payload + multipart overhead
    if "MAX_CONTENT_LENGTH" not in app.config:
        app.config["MAX_CONTENT_LENGTH"] = 100 * 1024  # 100KB

    if app.is_enabled(UseLazyLoading):
        location_obligatory_fields, _, location_model, app.db = _setup_location_model(app.db)
    else:
        location_obligatory_fields = []
        location_model = create_location_model([], {})
        app.db = extend_db_with_goodmap_queries(app.db, location_model)

    app.extensions["goodmap"] = {"location_obligatory_fields": location_obligatory_fields}

    field_renderers: dict[str, str] = {}
    for sc_name in app.shortcodes:
        field_renderers.setdefault(sc_name, sc_name)

    plugin_manifest = []
    for ep in importlib.metadata.entry_points(group=_PLUGIN_ENTRY_POINT_GROUP):
        bp, entry = _register_plugin_static_resources(ep)
        if bp is not None:
            app.register_blueprint(bp)
            plugin_manifest.append(entry)

    app.config["PLUGIN_MANIFEST"] = plugin_manifest

    CSRFProtect(app)

    # Create Attachment class for photo uploads
    # JPEG-only: universal browser/device support, good compression for location photos,
    # no transparency needed. PNG/WebP can be added if user demand warrants it.
    photo_attachment_config = AttachmentConfig(
        allowed_mime_types=frozenset({"image/jpeg"}),
        allowed_extensions=frozenset({"jpg", "jpeg"}),
        max_size=5 * 1024 * 1024,  # 5MB - reasonable for location photos
    )
    PhotoAttachment = create_attachment_class(photo_attachment_config)

    cp = core_pages(
        app.db,
        languages_dict(config.languages),
        app.notify,
        generate_csrf,
        location_model,
        photo_attachment_class=PhotoAttachment,
        photo_attachment_config=photo_attachment_config,
        feature_flags=config.feature_flags,
        field_renderers=field_renderers,
    )
    app.register_blueprint(cp)

    goodmap = Blueprint("goodmap", __name__, url_prefix="/", template_folder="templates")

    @goodmap.route("/")
    def index():
        """Render main map interface with location schema.

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

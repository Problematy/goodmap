"""Goodmap engine with location management and admin interface."""

import logging
import os

from flask import Blueprint, redirect, render_template, session
from flask_wtf.csrf import CSRFProtect, generate_csrf
from platzky import platzky
from platzky.attachment import create_attachment_class
from platzky.config import AttachmentConfig, languages_dict
from platzky.models import CmsModule

from goodmap.admin_api import admin_pages
from goodmap.config import GoodmapConfig
from goodmap.core_api import core_pages
from goodmap.data_models.location import create_location_model
from goodmap.db import (
    extend_db_with_goodmap_queries,
    get_location_obligatory_fields,
)

logger = logging.getLogger(__name__)


def create_app(config_path: str) -> platzky.Engine:
    """Create Goodmap application from YAML configuration file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        platzky.Engine: Configured Flask application
    """
    config = GoodmapConfig.parse_yaml(config_path)
    return create_app_from_config(config)


# TODO Checking if there is a feature flag secition should be part of configs logic not client app
def is_feature_enabled(config: GoodmapConfig, feature: str) -> bool:
    """Check if a feature flag is enabled in the configuration.

    Args:
        config: Goodmap configuration object
        feature: Name of the feature flag to check

    Returns:
        bool: True if feature is enabled, False otherwise
    """
    return config.feature_flags.get(feature, False) if config.feature_flags else False


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

    if is_feature_enabled(config, "USE_LAZY_LOADING"):
        location_obligatory_fields = get_location_obligatory_fields(app.db)
        # Extend db with goodmap queries first so we can use the bound method
        location_model = create_location_model(location_obligatory_fields, {})
        app.db = extend_db_with_goodmap_queries(app.db, location_model)

        # Use the extended db method directly (already bound by extend_db_with_goodmap_queries)
        try:
            category_data = app.db.get_category_data()  # type: ignore[attr-defined]
            categories = category_data.get("categories", {})
        except (KeyError, AttributeError):
            # Handle case where categories don't exist in the data
            categories = {}

        # Recreate location model with categories if we got them
        if categories:
            location_model = create_location_model(location_obligatory_fields, categories)
            app.db = extend_db_with_goodmap_queries(app.db, location_model)
    else:
        location_obligatory_fields = []
        categories = {}
        location_model = create_location_model(location_obligatory_fields, categories)
        app.db = extend_db_with_goodmap_queries(app.db, location_model)

    app.extensions["goodmap"] = {"location_obligatory_fields": location_obligatory_fields}

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

        location_schema = {  # TODO remove backward compatibility - deprecation
            "obligatory_fields": app.extensions["goodmap"][
                "location_obligatory_fields"
            ],  # Backward compatibility
            "categories": categories,  # Backward compatibility
            "fields": form_fields,
        }

        return render_template(
            "map.html",
            feature_flags=config.feature_flags,
            goodmap_frontend_lib_url=config.goodmap_frontend_lib_url,
            location_schema=location_schema,
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
        if not is_feature_enabled(config, "ENABLE_ADMIN_PANEL"):
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

    if is_feature_enabled(config, "ENABLE_ADMIN_PANEL"):
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

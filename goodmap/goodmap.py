import os

from flask import Blueprint, redirect, render_template, session
from flask_wtf.csrf import CSRFProtect, generate_csrf
from platzky import platzky
from platzky.config import languages_dict
from platzky.models import CmsModule

from goodmap.config import GoodmapConfig
from goodmap.core_api import core_pages
from goodmap.data_models.location import create_location_model
from goodmap.db import extend_db_with_goodmap_queries, get_location_obligatory_fields


def create_app(config_path: str) -> platzky.Engine:
    config = GoodmapConfig.parse_yaml(config_path)
    return create_app_from_config(config)


# TODO Checking if there is a feature flag secition should be part of configs logic not client app
def is_feature_enabled(config: GoodmapConfig, feature: str) -> bool:
    return config.feature_flags.get(feature, False) if config.feature_flags else False


def create_app_from_config(config: GoodmapConfig) -> platzky.Engine:
    directory = os.path.dirname(os.path.realpath(__file__))

    locale_dir = os.path.join(directory, "locale")
    config.translation_directories.append(locale_dir)
    app = platzky.create_app_from_config(config)

    if is_feature_enabled(config, "USE_LAZY_LOADING"):
        location_obligatory_fields = get_location_obligatory_fields(app.db)
    else:
        location_obligatory_fields = []

    location_model = create_location_model(location_obligatory_fields)

    app.db = extend_db_with_goodmap_queries(app.db, location_model)

    CSRFProtect(app)

    cp = core_pages(
        app.db,
        languages_dict(config.languages),
        app.notify,
        generate_csrf,
        location_model,
        feature_flags=config.feature_flags,
    )
    app.register_blueprint(cp)
    goodmap = Blueprint("goodmap", __name__, url_prefix="/", template_folder="templates")

    @goodmap.route("/")
    def index():
        return render_template(
            "map.html",
            feature_flags=config.feature_flags,
            goodmap_frontend_lib_url=config.goodmap_frontend_lib_url,
        )

    @goodmap.route("/goodmap-admin")
    def admin():
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

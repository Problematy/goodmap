import os

from flask import Blueprint, render_template
from flask_wtf.csrf import CSRFProtect, generate_csrf
from platzky import platzky
from platzky.config import Config, languages_dict

from goodmap.core_api import core_pages
from goodmap.data_models.location import create_location_model
from goodmap.db import extend_db_with_goodmap_queries, get_location_obligatory_fields


def create_app(config_path: str) -> platzky.Engine:
    config = Config.parse_yaml(config_path)
    return create_app_from_config(config)


# TODO Checking if there is a feature flag secition should be part of configs logic not client app
def is_feature_enabled(config: Config, feature: str) -> bool:
    return config.feature_flags.get(feature, False) if config.feature_flags else False


def create_app_from_config(config: Config) -> platzky.Engine:
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
        app.db, languages_dict(config.languages), app.notify, generate_csrf, location_model
    )
    app.register_blueprint(cp)
    goodmap = Blueprint("goodmap", __name__, url_prefix="/", template_folder="templates")

    @goodmap.route("/")
    def index():
        return render_template("map.html", feature_flags=config.feature_flags)

    app.register_blueprint(goodmap)
    return app

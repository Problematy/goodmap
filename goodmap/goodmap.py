import os

from flask import Blueprint, render_template
from flask_wtf.csrf import CSRFProtect, generate_csrf
from platzky import platzky
from platzky.config import Config, languages_dict

from goodmap.core_api import core_pages
from goodmap.data_models.location import create_location_model
from goodmap.db import get_data, get_location, get_locations


def get_location_obligatory_fields() -> list[tuple[str, type]]:
    if True:  # TODO Change condition based on feature flag when feature flags are implemented
        # TODO this should be fetched from the database
        return [("name", str), ("accessible_by", list[str]), ("type_of_place", str)]
    else:
        return []


def create_app(config_path: str) -> platzky.Engine:
    config = Config.parse_yaml(config_path)
    return create_app_from_config(config)


def create_app_from_config(config: Config) -> platzky.Engine:
    directory = os.path.dirname(os.path.realpath(__file__))

    location_model = create_location_model(get_location_obligatory_fields())

    locale_dir = os.path.join(directory, "locale")
    config.translation_directories.append(locale_dir)
    app = platzky.create_app_from_config(config)
    app.db.extend("get_data", get_data(app.db))
    app.db.extend("get_locations", get_locations(app.db, location_model))
    app.db.extend("get_location", get_location(app.db, location_model))

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

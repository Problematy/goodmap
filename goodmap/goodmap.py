import os

from flask import Blueprint, render_template
from flask_wtf.csrf import CSRFProtect, generate_csrf
from platzky import platzky
from platzky.config import Config, languages_dict

from .core_api import core_pages
from .db import get_data


def create_app(config_path: str) -> platzky.Engine:
    config = Config.parse_yaml(config_path)
    return create_app_from_config(config)


def create_app_from_config(config: Config) -> platzky.Engine:
    directory = os.path.dirname(os.path.realpath(__file__))
    locale_dir = os.path.join(directory, "locale")
    config.translation_directories.append(locale_dir)
    app = platzky.create_app_from_config(config)
    app.db.extend("get_data", get_data(app.db))

    CSRFProtect(app)

    cp = core_pages(app.db, languages_dict(config.languages), app.notify, generate_csrf)
    app.register_blueprint(cp)
    goodmap = Blueprint("goodmap", __name__, url_prefix="/", template_folder="templates")

    @goodmap.route("/")
    def index():
        return render_template("map.html", is_suggest_location_enabled=config.is_suggest_location_enabled)

    app.register_blueprint(goodmap)
    return app

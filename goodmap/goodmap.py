from functools import partial

from flask import Blueprint, redirect, render_template
from flask_wtf.csrf import CSRFProtect, generate_csrf

from goodmap.config import Config, languages_dict
from goodmap.platzky import platzky

from .core_api import core_pages
from .db import get_db_specific_get_data


def create_app(config_path: str) -> platzky.Engine:
    config = Config.parse_yaml(config_path)
    return create_app_from_config(config)


def create_app_from_config(config: Config) -> platzky.Engine:
    app = platzky.create_app_from_config(config)
    specific_get_data = get_db_specific_get_data(type(app.db).__name__)
    app.db.get_data = partial(specific_get_data, app.db)
    CSRFProtect(app)

    cp = core_pages(app.db, languages_dict(config.languages), app.notify, generate_csrf)
    app.register_blueprint(cp)
    goodmap = Blueprint("goodmap", __name__, url_prefix="/", template_folder="templates")
    for source, destination in config.route_overwrites.items():

        @goodmap.route(source)
        def testing_map():
            return redirect(destination)

    @goodmap.route("/")
    def index():
        return render_template("map.html")

    app.register_blueprint(goodmap)
    return app

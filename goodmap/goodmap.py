from flask import Blueprint, Flask, redirect, render_template

from goodmap.config import Config
from goodmap.platzky import platzky

from .core_api import core_pages


def create_app(config_path: str) -> Flask:
    config = Config.parse_yaml(config_path)

    app = platzky.create_app_from_config(config)
    app.register_blueprint(core_pages(app.db, config.languages_dict))  # pyright: ignore
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

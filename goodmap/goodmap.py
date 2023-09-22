import json

from flask import Blueprint, Flask, redirect, render_template

from goodmap.config import Config, languages_dict
from goodmap.platzky import platzky
from goodmap.platzky.db.google_json_db import GoogleJsonDb
from goodmap.platzky.db.json_db import Json
from goodmap.platzky.db.json_file_db import JsonFile

from .core_api import core_pages


def create_app(config_path: str) -> Flask:
    config = Config.parse_yaml(config_path)
    return create_app_from_config(config)

#TODO this should be dynamic, based on config, not hardcoded
def get_db_specific_get_data(db_type):
    mapping = {
        "GoogleJsonDb": google_json_get_data,
        "JsonFile": local_json_get_data,
        "Json": json_get_data,
    }
    classname = db_type
    return mapping[classname]

def create_app_from_config(config: Config) -> Flask:
    app = platzky.create_app_from_config(config)
    specific_get_data = get_db_specific_get_data(type(app.db).__name__)
    app.db.get_data = lambda : specific_get_data(app.db)

    cp = core_pages(app.db, languages_dict(config.languages), app.notify)  # pyright: ignore
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


def google_json_get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]


def local_json_get_data(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]


def json_get_data(self):
    return self.data

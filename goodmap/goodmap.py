import json
import types

from flask import Blueprint, Flask, redirect, render_template

from goodmap.services.email_service.email_service import EmailService
from goodmap.config import Config
from goodmap.platzky import platzky
from goodmap.platzky.db.google_json_db import GoogleJsonDb
from goodmap.platzky.db.json_file_db import JsonFile

from .core_api import core_pages


def create_app(config_path: str) -> Flask:
    config = Config.parse_yaml(config_path)

    app = platzky.create_app_from_config(config)
    app.email_service = EmailService(app.config["SMTP"], app.sendmail) if 'sendmail' in app.config["PLUGINS"] else None

    mapping = {GoogleJsonDb: google_json_get_data, JsonFile: local_json_get_data}
    app.db.get_data = types.MethodType(mapping[type(app.db)], app.db)  # pyright: ignore

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


def google_json_get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]


def local_json_get_data(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]

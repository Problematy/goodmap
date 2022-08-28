from flask import Flask, render_template, request, redirect, session, url_for
from flask_babel import Babel
import yaml
import sys

from .db import get_db
from .core_api import core_pages


def create_app(config_path="./config.yml"):
    app = Flask(__name__)

    app_config = load_app_config_from(config_path)

    app.config["config"] = app_config
    app.config["SECRET_KEY"] = app_config["flask_secretkey"]

    db_config = app_config["db"]
    app_db = get_db(db_config)
    app.db = app_db

    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "../translations"
    languages_config = app_config["languages"]

    core_api_handle = core_pages(app.db, languages_config)
    app.register_blueprint(core_api_handle)

    app.babel = Babel(app)

    if overwrites := app_config.get("route_overwrites"):
        for source, destination in overwrites.items():

            @app.route(source)
            def testing_map():
                return redirect(destination)

    @app.babel.localeselector
    def get_locale():
        return session.get(
            "language",
            request.accept_languages.best_match(app_config["languages"]),
        )

    @app.route("/language/<language>")
    def set_language(language):
        session["language"] = language
        return redirect(url_for("index"))

    @app.context_processor
    def setup_context():
        return dict(app_name=app_config["app_name"])

    @app.route("/")
    def index():
        return render_template("map.html")

    return app


def load_app_config_from(config_path):
    app_config = load_yaml_from(config_path)
    validate_app_config(app_config)
    return app_config


def load_yaml_from(config_path):
    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        sys.exit(
            "ERROR: Expected but not found: file or directory '{}'. Check README.md for more info!".format(
                config_path
            )
        )


def validate_app_config(app_config):
    if not "flask_secretkey" in app_config:
        sys.exit(
            "ERROR Application misconfigured: please, set 'flask_secretkey' in './config.yml'"
        )

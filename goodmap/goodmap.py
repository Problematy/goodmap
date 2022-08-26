from flask import Flask, render_template, request, redirect, session, url_for
from flask_babel import Babel
import yaml
import sys

from .db import get_db
from .core_api import core_pages


def create_app(config_path="./config.yml"):
    app = Flask(__name__)

    app.config["config"] = load_config(config_path)
    if not "flask_secretkey" in app.config["config"]:
        sys.exit(
            "ERROR Application misconfigured: please, set 'flask_secretkey' in './config.yml'"
        )
    app.config["SECRET_KEY"] = app.config["config"]["flask_secretkey"]
    app.db = get_db(app.config["config"]["db"])
    app.config["BABEL_DEFAULT_LOCALE"] = app.config["config"]["languages"][0]
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "../translations"
    app.register_blueprint(core_pages(app.db, app.config["config"]["languages"]))

    app.babel = Babel(app)

    if overwrites := app.config["config"].get("route_overwrites"):
        for source, destination in overwrites.items():

            @app.route(source)
            def testing_map():
                return redirect(destination)

    @app.babel.localeselector
    def get_locale():
        return session.get(
            "language",
            request.accept_languages.best_match(app.config["config"]["languages"]),
        )

    @app.route("/language/<language>")
    def set_language(language):
        session["language"] = language
        return redirect(url_for("index"))

    @app.context_processor
    def setup_context():
        return dict(app_name=app.config["config"]["app_name"])

    @app.route("/")
    def index():
        return render_template("map.html")

    return app


def load_config(config_path):
    try:
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        sys.exit(
            "ERROR: Expected but not found: file or directory '{}'. Check README.md for more info!".format(
                config_path
            )
        )

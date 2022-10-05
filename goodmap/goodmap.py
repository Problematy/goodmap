from flask import Flask, render_template, request, redirect, session, url_for
from flask_babel import Babel
import yaml
import os

from .db import get_db
from .core_api import core_pages


def create_app(config_path):
    app = Flask(__name__)
    absolute_config_path = os.path.join(os.getcwd(), config_path)
    app.config.from_file(absolute_config_path, load=yaml.safe_load)

    app.db = get_db(app.config["DB"])
    app.register_blueprint(core_pages(app.db, app.config["LANGUAGES"]))
    app.babel = Babel(app)

    if overwrites := app.config.get("ROUTE_OVERWRITES"):
        for source, destination in overwrites.items():
            @app.route(source)
            def testing_map():
                return redirect(destination)

    @app.babel.localeselector
    def get_locale():
        return session.get('language', request.accept_languages.best_match(app.config["LANGUAGES"]))

    @app.route('/language/<language>')
    def set_language(language):
        session['language'] = language
        return redirect(url_for('index'))

    @app.context_processor
    def setup_context():
        return dict(app_name=app.config['APP_NAME'])

    @app.route("/")
    def index():
        return render_template('map.html')

    return app

from flask import Flask, render_template, request, redirect, jsonify
from flask_babel import Babel, gettext
import yaml

from .db import get_db
from .formatter import prepare_pin
from .checker import checker_page


def does_fulfill_requirement(entry, requirements):
    matches = []
    for category, values in requirements:
        if not values:
            continue
        matches.append(all(entry_value in entry[category] for entry_value in values))
    return all(matches)


def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def create_app(config_path="./config.yml"):
    app = Flask(__name__)

    app.config["config"] = load_config(config_path)
    app.config["SECRET_KEY"] = app.config["config"]["flask_secretkey"]
    app.db = get_db(app.config["config"]["db"])
    app.config['BABEL_DEFAULT_LOCALE'] = 'pl'
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "../translations"
    app.register_blueprint(checker_page(app.db))
    app.babel = Babel(app)

    if overwrites := app.config["config"].get("development_overwrites"):
        for source, destination in overwrites.items():
            @app.route(source)
            def testing_map():
                return redirect(destination)

    @app.babel.localeselector
    def get_locale():
        return 'pl'

    @app.context_processor
    def setup_context():
        return dict(app_name=app.config['config']['app_name'])

    @app.route("/")
    def index():
        return render_template('map.html')

    @app.route("/api/data")
    def get_data():
        all_data = app.db.get_data()
        local_data = all_data["data"]
        query_params = request.args.to_dict(flat=False)
        categories = all_data["categories"]
        requirements = []
        for key in categories.keys():
            requirements.append((key, query_params.get(key)))

        filtered_data = filter(lambda x: does_fulfill_requirement(x, requirements), local_data)
        formatted_data = map(lambda x: prepare_pin(x, all_data["visible_data"]), filtered_data)
        return jsonify(list(formatted_data))

    @app.route("/api/categories")
    def get_categories():
        all_data = app.db.get_data()
        categories = list(all_data["categories"].keys())
        return jsonify(categories)

    @app.route("/api/category/<category_type>")
    def get_category_types(category_type):
        all_data = app.db.get_data()
        local_data = all_data["categories"][category_type]
        return jsonify(local_data)
    return app

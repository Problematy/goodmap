from flask import Flask
from flask import render_template, request, current_app
import os
import json
from flask import jsonify


def load_json(file):
    with open(file, 'r') as file:
        return json.load(file)


def does_fulfill_requriement(entry, requirements):
    matches = []
    for filter_type, values in requirements:
        if not values:
            continue
        matches.append(all(entry_value in entry[filter_type] for entry_value in values))
    return all(matches)


def create_app():
    app = Flask(__name__)
    DATA = os.getenv('DATA')
    app.config['data'] = load_json(DATA)

    @app.route("/")
    def index():
        return render_template('map.html')

    @app.route("/data")
    def get_data():
        local_data = app.config["data"]["data"]
        query_params = request.args.to_dict(flat=False)
        filters = app.config["data"]["filters"]
        requirements = []
        for x in filters.keys():
            requirements.append((x, query_params.get(x)))

        filtered_data = filter(lambda x: does_fulfill_requriement(x, requirements), local_data)
        return jsonify(list(filtered_data))

    @app.route("/types")
    def get_types():
        local_data = app.config["data"]["filters"]["types"]
        return jsonify(local_data)

    return app

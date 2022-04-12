from flask import Flask
from flask import render_template, request
import os
import json
from flask import jsonify


app = Flask(__name__)
DATA = os.getenv('DATA')


def get_data(file):
    with open(file, 'r') as file:
        return json.load(file)


data = get_data(DATA)

@app.route("/")
def index():
    return render_template('map.html')


@app.route("/data")
def get_data():
    local_data = data["data"]
    query_params = request.args.to_dict(flat=False)
    what = query_params.get('type')
    if what:
        filtered_data = filter(lambda x: all(elem in x["types"] for elem in what), local_data)
        return jsonify(list(filtered_data))
    else:
        return jsonify(local_data)


@app.route("/types")
def get_types():
    local_data = data["types"]
    return jsonify(local_data)

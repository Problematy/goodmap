from flask import Flask
from flask import render_template
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
def map_data():
    return jsonify(data)

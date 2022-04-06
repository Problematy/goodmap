from flask import Flask
from flask import render_template
import os
import json
from flask import jsonify


app = Flask(__name__)

DATA = os.getenv('DATA')

with open(DATA, 'r') as f:
    data = json.load(f)


@app.route("/")
def index():
    return render_template('map.html')


@app.route("/data")
def map_data():
    return jsonify(data)

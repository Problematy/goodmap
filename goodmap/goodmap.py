from flask import Flask
from flask import render_template
import os
import json
from flask import jsonify


app = Flask(__name__)

DATA = os.getenv('DATA')




@app.route("/")
def index():
    return render_template('map.html')


@app.route("/data")
def map_data():
    with open(DATA, 'r') as f:
        data = json.load(f)
    return jsonify(data)

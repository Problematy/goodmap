import json

from platzky.db import json_file_db


def get_data(self):
    with open(self.data_file_path, 'r') as file:
        return json.load(file)["map"]


def process():
    json_file_db.JsonFile.get_data = get_data

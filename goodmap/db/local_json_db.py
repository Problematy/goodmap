from .db_base import Database
import json


def load_json(json_config):
    with open(json_config["data_file_path"], 'rw') as file:
        return json.load(file)


class LocalJsonDb(Database):
    def __init__(self, config):
        self.data_file_path = config["data_file_path"]

    def get_data(self):
        with open(self.data_file_path, 'r') as file:
            return json.load(file)

    def save_entry(self, entry):
        data = self.get_data()
        with open(self.data_file_path, 'w') as file:
            data["data"].append(entry)
            json.dump(data, file, indent=4)

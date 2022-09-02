from .db_base import Database
import json


class LocalJsonDb(Database):
    def __init__(self, config):
        self.data_file_path = config["DATA_FILE_PATH"]

    def get_data(self):
        with open(self.data_file_path, 'r') as file:
            return json.load(file)

    def save_entry(self, entry):
        data = self.get_data()
        with open(self.data_file_path, 'w') as file:
            data["data"].append(entry)
            json.dump(data, file, indent=4)

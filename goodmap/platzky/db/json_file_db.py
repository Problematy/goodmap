import json
import os.path

from goodmap.config import JsonFileDbConfig
from goodmap.platzky.db.json_db import Json


def get_db(config: JsonFileDbConfig):
    db_path = os.path.abspath(config.path)
    return JsonFile(db_path)


class JsonFile(Json):
    def __init__(self, file_path):
        self.data_file_path = file_path
        with open(self.data_file_path) as json_file:
            data = json.load(json_file)
            super().__init__(data)

    def _save_file(self):
        with open(self.data_file_path, "w") as json_file:
            json.dump(self.data, json_file)

    def add_comment(self, author_name, comment, post_slug):
        super().add_comment(author_name, comment, post_slug)
        self._save_file()

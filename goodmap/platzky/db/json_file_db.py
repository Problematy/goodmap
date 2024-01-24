import json

from pydantic import Field

from .db import DBConfig
from .json_db import Json


def db_type():
    return JsonFile


def db_config_type():
    return JsonFileDbConfig


class JsonFileDbConfig(DBConfig):
    path: str = Field(alias="PATH")


def get_db(config):
    json_file_db_config = JsonFileDbConfig.parse_obj(config)
    return JsonFile(json_file_db_config.path)


def db_from_config(config: JsonFileDbConfig):
    return JsonFile(config.path)


class JsonFile(Json):
    def __init__(self, path: str):
        self.data_file_path = path
        with open(self.data_file_path) as json_file:
            data = json.load(json_file)
            super().__init__(data)
        self.module_name = "json_file_db"
        self.db_name = "JsonFileDb"

    def _save_file(self):
        with open(self.data_file_path, "w") as json_file:
            json.dump(self.data, json_file)

    def add_comment(self, author_name, comment, post_slug):
        super().add_comment(author_name, comment, post_slug)
        self._save_file()

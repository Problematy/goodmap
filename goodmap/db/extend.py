import types

from goodmap.db import google_json_db, local_json_db
from goodmap.platzky.db.google_json_db import GoogleJsonDb
from goodmap.platzky.db.json_file_db import JsonFile


def extend_app_db(app):
    mapping = {GoogleJsonDb: google_json_db.get_data, JsonFile: local_json_db.get_data}

    app.db.get_data = types.MethodType(mapping[type(app.db)], app.db)

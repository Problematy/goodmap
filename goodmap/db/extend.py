import types

from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_file_db import JsonFile

from goodmap.db import google_json_db, local_json_db


def extend_app_db(app):
    mapping = {
        GoogleJsonDb: google_json_db.get_data,
        JsonFile: local_json_db.get_data
    }


    app.db.get_data = types.MethodType(mapping[type(app.db)], app.db)

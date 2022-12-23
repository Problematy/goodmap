from google.cloud import storage
import json
from platzky.db.google_json_db import GoogleJsonDb


def get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]


def process():
    json_file_db.GoogleJsonDb.get_data = get_data

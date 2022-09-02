from google.cloud import storage
import json

from .db_base import Database


def get_blob(bucket_name, source_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    return bucket.blob(source_blob_name)


class GoogleJsonDb(Database):
    def __init__(self, config):
        self.blob = get_blob(config["BUCKET_NAME"], config["SOURCE_BLOB_NAME"])

    def get_data(self):
        raw_data = self.blob.download_as_text(client=None)
        return json.loads(raw_data)

    def save_entry(self, entry):
        data = self.get_data()
        data["data"].append(entry)
        self.blob.upload_from_string(json.dumps(data), content_type='application/json')

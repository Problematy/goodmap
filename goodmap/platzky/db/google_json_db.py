import json
from google.cloud import storage
from .json_db import Json


def get_db(app_config):
    config = app_config["DB"]
    bucket_name = config["BUCKET_NAME"]
    source_blob_name = config["SOURCE_BLOB_NAME"]
    return GoogleJsonDb(bucket_name, source_blob_name)


def get_blob(bucket_name, source_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    return bucket.blob(source_blob_name)


def get_data(blob):
    raw_data = blob.download_as_text(client=None)
    return json.loads(raw_data)


class GoogleJsonDb(Json):
    def __init__(self, bucket_name, source_blob_name):
        self.blob = get_blob(bucket_name, source_blob_name)
        data = get_data(self.blob)
        super().__init__(data)

    def save_entry(self, entry):
        data = get_data(self.blob)
        data["data"].append(entry)
        self.blob.upload_from_string(json.dumps(data), content_type='application/json')

import json

from google.cloud.storage import Client
from pydantic import Field

from goodmap.platzky.db.db import DBConfig
from goodmap.platzky.db.json_db import Json


def db_type():
    return GoogleJsonDb


def db_config_type():
    return GoogleJsonDbConfig


class GoogleJsonDbConfig(DBConfig):
    bucket_name: str = Field(alias="BUCKET_NAME")
    source_blob_name: str = Field(alias="SOURCE_BLOB_NAME")


def db_from_config(config: GoogleJsonDbConfig):
    return GoogleJsonDb(config.bucket_name, config.source_blob_name)


def get_db(config):
    google_json_db_config = GoogleJsonDbConfig.parse_obj(config)
    return GoogleJsonDb(google_json_db_config.bucket_name, google_json_db_config.source_blob_name)


def get_blob(bucket_name, source_blob_name):
    storage_client = Client()
    bucket = storage_client.bucket(bucket_name)
    return bucket.blob(source_blob_name)


def get_data(blob):
    raw_data = blob.download_as_text(client=None)
    return json.loads(raw_data)


class GoogleJsonDb(Json):
    def __init__(self, bucket_name, source_blob_name):
        self.bucket_name = bucket_name
        self.source_blob_name = source_blob_name

        self.blob = get_blob(self.bucket_name, self.source_blob_name)
        data = get_data(self.blob)
        super().__init__(data)

        self.module_name = "google_json_db"
        self.db_name = "GoogleJsonDb"

    def save_entry(self, entry):
        data = get_data(self.blob)
        data["data"].append(entry)
        self.blob.upload_from_string(json.dumps(data), content_type="application/json")

from google.cloud import storage
import json


def load_google_hosted_json_db(json_config):
    return json.loads(download_blob(json_config["bucket_name"], json_config["source_blob_name"]))


def download_blob(bucket_name, source_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    return blob.download_as_string(client=None)

import io
import json

from google.cloud import storage

from problematy import settings


def get_gcs_client():
    return storage.Client()


def get_blob(bucket_name, source_blob_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    return bucket.blob(source_blob_name)


def download_blob(blob_name):
    blob = get_blob(settings.APPLICATION_BUCKET_NAME, blob_name)
    return json.loads(blob.download_as_text(encoding="utf-8"))


def upload_blob(file: io.BytesIO, blob_name: str):
    blob = get_blob(settings.APPLICATION_BUCKET_NAME, blob_name)
    blob.upload_from_file(file)
from django.http import JsonResponse

from gcs_config import download_blob
from problematy import settings


def download_locations(request):
    data = download_blob(settings.LOCATIONS_BLOB_PATH)
    return JsonResponse(data, safe=False)

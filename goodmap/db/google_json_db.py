import json


def get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]

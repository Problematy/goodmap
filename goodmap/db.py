import json

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


def google_json_get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]


def local_json_get_data(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]


def json_get_data(self):
    return self.data


def get_db_specific_get_data(db_type):
    mapping = {
        "GoogleJsonDb": google_json_get_data,
        "JsonFile": local_json_get_data,
        "Json": json_get_data,
    }
    return mapping[db_type]

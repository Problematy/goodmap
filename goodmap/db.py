import json

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


def google_json_db_get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]


def json_file_db_get_data(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]


def json_db_get_data(self):
    return self.data


def get_data(db):
    function_name = f"{db.module_name}_get_data"
    return globals()[function_name]

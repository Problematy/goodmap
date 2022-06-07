import json


def load_json(file):
    with open(file, 'r') as file:
        return json.load(file)


def load_json_db(json_config):
    with open(json_config["data_file_path"], 'r') as file:
        return json.load(file)

    return load_json(json_config["data_file_path"])

from .local_json_db import load_json_db
from .google_json_db import load_google_hosted_json_db


def load_data(db_config):
    config_loaders = {
        "json_file": lambda x: load_json_db(x),
        "google_hosted_json_file": lambda x: load_google_hosted_json_db(x)
    }
    return config_loaders[db_config["type"]](db_config)

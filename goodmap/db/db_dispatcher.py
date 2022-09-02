from .local_json_db import LocalJsonDb
from .google_json_db import GoogleJsonDb


def get_db(db_config):
    config_loaders = {
        "json_file": lambda x: LocalJsonDb(x),
        "google_hosted_json_file": lambda x: GoogleJsonDb(x)
    }
    return config_loaders[db_config["TYPE"]](db_config)

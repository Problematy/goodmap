from .local_json_db import LocalJsonDb
from .google_json_db import GoogleJsonDb


def get_db(db_config):
    db_loaders = {
        "json_file": lambda local: LocalJsonDb(local),
        "google_hosted_json_file": lambda hosted: GoogleJsonDb(hosted),
    }

    db_type = db_config["type"]
    selected_db_loader = db_loaders[db_type]
    return selected_db_loader(db_config)

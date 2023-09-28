import importlib.util
import os
import sys
from os.path import abspath, dirname


def get_db(db_config):
    db_dir = dirname(abspath(__file__))
    db_name = db_config["TYPE"]

    spec = importlib.util.spec_from_file_location(db_name, os.path.join(db_dir, f"{db_name}_db.py"))

    assert spec is not None
    db = importlib.util.module_from_spec(spec)
    sys.modules[f"{db_name}_db"] = db
    assert spec.loader is not None
    spec.loader.exec_module(db)

    return db.get_db(db_config)

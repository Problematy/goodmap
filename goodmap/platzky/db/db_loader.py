import importlib.util
import os
import sys
from os.path import abspath, dirname


def get_db(db_config):
    db_name = db_config.type
    db = get_db_module(db_name)
    return db.db_from_config(db_config)


def get_db_module(db_type):
    """
    Load db module from db_type
    This function is used to load db module dynamically as it is specified in config file.
    :param db_type: name of db module
    :return: db module
    """
    db_dir = dirname(abspath(__file__))
    spec = importlib.util.spec_from_file_location(f"goodmap.platzky.db.{db_type}", os.path.join(db_dir, f"{db_type}_db.py"))  # TODO remove goodmap from path
    assert spec is not None
    db = importlib.util.module_from_spec(spec)
    sys.modules[f"{db_type}_db"] = db
    assert spec.loader is not None
    spec.loader.exec_module(db)


    return db

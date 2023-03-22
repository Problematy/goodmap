from os.path import dirname

from flask import Flask

from goodmap.platzky import config
from goodmap.platzky.platzky import create_engine_from_config


def test_engine_creation():
    mapping = {
        "DB": {
            "TYPE": "json_file",
            "PATH": f"{dirname(__file__)}/../../e2e_tests/e2e_test_data.json",
        }
    }
    engine = create_engine_from_config(config.from_mapping(mapping))
    assert type(engine) == Flask

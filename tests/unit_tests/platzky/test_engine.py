from os.path import dirname

from flask import Flask

from goodmap.config import Config
from goodmap.platzky.platzky import create_engine_from_config


def test_engine_creation():
    config = Config.parse_obj(
        {
            "APP_NAME": "testingApp",
            "SECRET_KEY": "secret",
            "DB": {
                "TYPE": "json_file",
                "PATH": f"{dirname(__file__)}/../../e2e_tests/e2e_test_data.json",
            },
        }
    )
    engine = create_engine_from_config(config)
    assert type(engine) == Flask

from goodmap.platzky.config import from_mapping, Config
import pytest


def test_config_creation_with_incorrect_mappings():
    wrong_mappings = {
        "empty_mapping": {},
        "db_without_type": {'DB': 'anything'},
        "db_type_wrong": {'DB': {'TYPE': 'wrong-type'}}
    }

    for _, mapping in wrong_mappings.items():
        with pytest.raises(Exception):
            from_mapping(mapping)


def test_config_creation_from_file():
    not_empty_dict = {'DB': {'TYPE': 'json_file',
                             "PATH": "./tests/e2e_tests/db.json"}}
    config = from_mapping(not_empty_dict)
    assert type(config) == Config

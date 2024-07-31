import json
from unittest.mock import mock_open, patch

from goodmap.data_validator import (
    get_pts_with_invalid_values_in_categories,
    get_pts_with_missing_obligatory_fields,
    get_pts_with_null_values,
    validate_from_json,
    validate_from_json_file,
)

obligatory_fields = ["position", "name", "accessible_by", "type_of_place", "UUID"]
categories = {
    "accessible_by": ["bikes", "cars", "pedestrians"],
    "type_of_place": ["big bridge", "small bridge"],
}


fully_valid_database = {
    "map": {
        "data": [
            {
                "name": "Grunwaldzki",
                "position": [51.1095, 17.0525],
                "accessible_by": ["pedestrians", "cars"],
                "type_of_place": "big bridge",
                "UUID": "hidden",
            },
            {
                "name": "Zwierzyniecka",
                "position": [51.10655, 17.0555],
                "accessible_by": ["bikes", "pedestrians"],
                "type_of_place": "small bridge",
                "UUID": "dattarro",
            },
        ],
        "obligatory_fields": ["position", "name", "accessible_by", "type_of_place", "UUID"],
        "categories": {
            "accessible_by": ["bikes", "cars", "pedestrians"],
            "type_of_place": ["big bridge", "small bridge"],
        },
        "visible_data": ["accessible_by", "type_of_place"],
        "meta_data": ["UUID"],
    },
    "site_content": {},
    "plugins": [],
}

empty_list_of_invalid_points = []

missing_obligatory_fields_data = [
    {
        "name": "Grunwaldzki",
        "position": [51.1095, 17.0525],
        "accessible_by": ["pedestrians", "cars"],
        "UUID": "hidden",
    },
    {
        "position": [51.10655, 17.0555],
        "type_of_place": "small bridge",
        "accessible_by": ["bikes", "pedestrians"],
        "UUID": "dattarro",
    },
]

pts_with_missing_obligatory_fields = [
    (
        "missing obligatory field",
        {
            "name": "Grunwaldzki",
            "position": [51.1095, 17.0525],
            "accessible_by": ["pedestrians", "cars"],
            "UUID": "hidden",
        },
        "type_of_place",
    ),
    (
        "missing obligatory field",
        {
            "position": [51.10655, 17.0555],
            "type_of_place": "small bridge",
            "accessible_by": ["bikes", "pedestrians"],
            "UUID": "dattarro",
        },
        "name",
    ),
]

invalid_values_in_categories_data = [
    {
        "name": "Grunwaldzki",
        "position": [51.1095, 17.0525],
        "accessible_by": ["pedestrians", "cars"],
        "type_of_place": "vacuum cleaners shop",
        "UUID": "hidden",
    },
    {
        "name": "Zwierzyniecka",
        "position": [51.10655, 17.0555],
        "accessible_by": ["bikes", "penguins"],
        "type_of_place": "small bridge",
        "UUID": "dattarro",
    },
]

pts_with_invalid_values_in_categories = [
    (
        "invalid value in category",
        {
            "name": "Grunwaldzki",
            "position": [51.1095, 17.0525],
            "accessible_by": ["pedestrians", "cars"],
            "type_of_place": "vacuum cleaners shop",
            "UUID": "hidden",
        },
        "type_of_place",
    ),
    (
        "invalid value in category",
        {
            "name": "Zwierzyniecka",
            "position": [51.10655, 17.0555],
            "accessible_by": ["bikes", "penguins"],
            "type_of_place": "small bridge",
            "UUID": "dattarro",
        },
        "accessible_by",
    ),
]

null_values_data = [
    {
        "name": "Grunwaldzki",
        "position": [51.1095, 17.0525],
        "accessible_by": ["pedestrians", "cars"],
        "type_of_place": "big bridge",
        "UUID": None,
    },
    {
        "name": "Zwierzyniecka",
        "position": [51.10655, 17.0555],
        "accessible_by": ["bikes", "pedestrians"],
        "type_of_place": "small bridge",
        "UUID": "dattarro",
        "website": None,
    },
]

pts_with_null_values = [
    (
        "null value",
        {
            "name": "Grunwaldzki",
            "position": [51.1095, 17.0525],
            "accessible_by": ["pedestrians", "cars"],
            "type_of_place": "big bridge",
            "UUID": None,
        },
        "UUID",
    ),
    (
        "null value",
        {
            "name": "Zwierzyniecka",
            "position": [51.10655, 17.0555],
            "accessible_by": ["bikes", "pedestrians"],
            "type_of_place": "small bridge",
            "UUID": "dattarro",
            "website": None,
        },
        "website",
    ),
]


def test_validator_returns_empty_list_on_valid_data():
    assert validate_from_json(fully_valid_database) == empty_list_of_invalid_points


def test_validator_returns_points_missing_obligatory_fields():
    assert (
        get_pts_with_missing_obligatory_fields(missing_obligatory_fields_data, obligatory_fields)
        == pts_with_missing_obligatory_fields
    )


def test_validator_returns_points_with_invalid_value_in_category():
    assert (
        get_pts_with_invalid_values_in_categories(invalid_values_in_categories_data, categories)
        == pts_with_invalid_values_in_categories
    )


def test_validator_returns_points_with_null_values():
    assert get_pts_with_null_values(null_values_data) == pts_with_null_values


def test_validation_from_json_file():
    mock_file_path = "./tests/e2e_tests/e2e_test_data.json"
    mock_file_content = {
        "map": {
            "data": [
                {
                    "name": "Grunwaldzki",
                    "position": [51.1095, 17.0525],
                    "accessible_by": ["pedestrians", "cars"],
                    "UUID": "hidden",
                },
                {
                    "name": None,
                    "position": [51.10655, 17.0555],
                    "accessible_by": ["bikes", "pedestrians"],
                    "type_of_place": "small bridgeeeeeeeeee",
                    "UUID": "dattarro",
                },
            ],
            "obligatory_fields": ["position", "name", "accessible_by", "type_of_place", "UUID"],
            "categories": {
                "accessible_by": ["bikes", "cars", "pedestrians"],
                "type_of_place": ["big bridge", "small bridge"],
            },
            "visible_data": ["accessible_by", "type_of_place"],
            "meta_data": ["UUID"],
        },
        "site_content": {},
        "plugins": [],
    }

    expected_result = [
        (
            "missing obligatory field",
            {
                "name": "Grunwaldzki",
                "position": [51.1095, 17.0525],
                "accessible_by": ["pedestrians", "cars"],
                "UUID": "hidden",
            },
            "type_of_place",
        ),
        (
            "invalid value in category",
            {
                "name": None,
                "position": [51.10655, 17.0555],
                "accessible_by": ["bikes", "pedestrians"],
                "type_of_place": "small bridgeeeeeeeeee",
                "UUID": "dattarro",
            },
            "type_of_place",
        ),
        (
            "null value",
            {
                "name": None,
                "position": [51.10655, 17.0555],
                "accessible_by": ["bikes", "pedestrians"],
                "type_of_place": "small bridgeeeeeeeeee",
                "UUID": "dattarro",
            },
            "name",
        ),
    ]

    with patch("builtins.open", mock_open(read_data=json.dumps(mock_file_content))) as mock_file:
        result = validate_from_json_file(mock_file_path)
        assert result == expected_result
        mock_file.assert_called_once_with(mock_file_path)

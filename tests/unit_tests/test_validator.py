import json
from unittest.mock import mock_open, patch

from goodmap.data_validator import (
    FieldViolation,
    FormatViolation,
    ViolationType,
    report_data_violations_from_json,
    report_data_violations_from_json_file,
)

database_fully_valid = {
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
        "location_obligatory_fields": [
            "position",
            "name",
            "accessible_by",
            "type_of_place",
            "UUID",
        ],
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

empty_list_of_violations = []

database_missing_obligatory_fields = {
    "map": {
        "data": [
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
        ],
        "location_obligatory_fields": [
            "position",
            "name",
            "accessible_by",
            "type_of_place",
            "UUID",
        ],
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

violations_with_missing_obligatory_fields = [
    FieldViolation(
        ViolationType(1),
        {
            "name": "Grunwaldzki",
            "position": [51.1095, 17.0525],
            "accessible_by": ["pedestrians", "cars"],
            "UUID": "hidden",
        },
        "type_of_place",
    ),
    FieldViolation(
        ViolationType(1),
        {
            "position": [51.10655, 17.0555],
            "type_of_place": "small bridge",
            "accessible_by": ["bikes", "pedestrians"],
            "UUID": "dattarro",
        },
        "name",
    ),
]

database_invalid_values_in_categories = {
    "map": {
        "data": [
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
        ],
        "location_obligatory_fields": [
            "position",
            "name",
            "accessible_by",
            "type_of_place",
            "UUID",
        ],
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

violations_with_invalid_values_in_categories = [
    FieldViolation(
        ViolationType(2),
        {
            "name": "Grunwaldzki",
            "position": [51.1095, 17.0525],
            "accessible_by": ["pedestrians", "cars"],
            "type_of_place": "vacuum cleaners shop",
            "UUID": "hidden",
        },
        "type_of_place",
    ),
    FieldViolation(
        ViolationType(2),
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


database_null_values = {
    "map": {
        "data": [
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
        ],
        "location_obligatory_fields": [
            "position",
            "name",
            "accessible_by",
            "type_of_place",
            "UUID",
        ],
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

violations_with_null_values = [
    FieldViolation(
        ViolationType(3),
        {
            "name": "Grunwaldzki",
            "position": [51.1095, 17.0525],
            "accessible_by": ["pedestrians", "cars"],
            "type_of_place": "big bridge",
            "UUID": None,
        },
        "UUID",
    ),
    FieldViolation(
        ViolationType(3),
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


def test_validator_returns_empty_list_on_valid_database():
    assert report_data_violations_from_json(database_fully_valid) == empty_list_of_violations


def assert_violations_are_as_expected(reported_violations, expected_violations):
    assert len(reported_violations) == len(expected_violations)
    for idx, violation in enumerate(reported_violations):
        expected_violation = expected_violations[idx]
        assert violation.violation_type == expected_violation.violation_type
        assert violation.datapoint == expected_violation.datapoint
        assert violation.violating_field == expected_violation.violating_field


def test_validator_returns_points_missing_obligatory_fields():
    reported_violations = report_data_violations_from_json(database_missing_obligatory_fields)
    expected_violations = violations_with_missing_obligatory_fields
    assert_violations_are_as_expected(reported_violations, expected_violations)


def test_validator_returns_points_with_invalid_value_in_category():
    reported_violations = report_data_violations_from_json(database_invalid_values_in_categories)
    expected_violations = violations_with_invalid_values_in_categories
    assert_violations_are_as_expected(reported_violations, expected_violations)


def test_validator_returns_points_with_null_values():
    reported_violations = report_data_violations_from_json(database_null_values)
    expected_violations = violations_with_null_values
    assert_violations_are_as_expected(reported_violations, expected_violations)


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
            "location_obligatory_fields": [
                "position",
                "name",
                "accessible_by",
                "type_of_place",
                "UUID",
            ],
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

    expected_violations = [
        FieldViolation(
            ViolationType(1),
            {
                "name": "Grunwaldzki",
                "position": [51.1095, 17.0525],
                "accessible_by": ["pedestrians", "cars"],
                "UUID": "hidden",
            },
            "type_of_place",
        ),
        FieldViolation(
            ViolationType(2),
            {
                "name": None,
                "position": [51.10655, 17.0555],
                "accessible_by": ["bikes", "pedestrians"],
                "type_of_place": "small bridgeeeeeeeeee",
                "UUID": "dattarro",
            },
            "type_of_place",
        ),
        FieldViolation(
            ViolationType(3),
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
        reported_violations = report_data_violations_from_json_file(mock_file_path)
        assert_violations_are_as_expected(reported_violations, expected_violations)

        mock_file.assert_called_once_with(mock_file_path)


def test_invalid_format():
    mock_file_path = "./tests/e2e_tests/e2e_test_data.json"

    with patch("builtins.open", mock_open(read_data='{"map": }')) as mock_file:
        reported_violations = report_data_violations_from_json_file(mock_file_path)
        EXPECTED_NUMBER_OF_VIOLATIONS = 1
        assert len(reported_violations) == EXPECTED_NUMBER_OF_VIOLATIONS
        only_violation = reported_violations[0]
        assert isinstance(only_violation, FormatViolation)
        assert isinstance(only_violation.decoding_error, ValueError)
        mock_file.assert_called_once_with(mock_file_path)

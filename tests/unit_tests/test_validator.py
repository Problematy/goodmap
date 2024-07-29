from goodmap.data_validator import validate_from_json

fully_valid_data = {
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

fully_valid_msg = []

missing_obligatory_fields_data = {
    "map": {
        "data": [
            {
                "name": "Grunwaldzki",
                "position": [51.1095, 17.0525],
            },
            {"position": [51.10655, 17.0555], "type_of_place": "small bridge"},
        ],
        "obligatory_fields": [
            "position",
            "name",
            "type_of_place",
        ],
        "categories": {"type_of_place": ["big bridge", "small bridge"]},
    },
    "site_content": {},
    "plugins": [],
}

missing_obligatory_fields_msg = [
    (
        "missing obligatory field",
        {"name": "Grunwaldzki", "position": [51.1095, 17.0525]},
        "type_of_place",
    ),
    (
        "missing obligatory field",
        {"position": [51.10655, 17.0555], "type_of_place": "small bridge"},
        "name",
    ),
]

invalid_category_value_data = {
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

invalid_category_value_msg = [
    (
        "invalid category value",
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
        "invalid category value",
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

null_values_data = {
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
        "obligatory_fields": ["position", "name", "accessible_by", "type_of_place", "UUID"],
        "categories": {
            "accessible_by": ["bikes", "cars", "pedestrians"],
            "type_of_place": ["big bridge", "small bridge"],
        },
    },
}

null_values_msg = [
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


def test_fully_valid_data():
    assert validate_from_json(fully_valid_data) == fully_valid_msg


def test_obligagory_fields_present():
    assert validate_from_json(missing_obligatory_fields_data) == missing_obligatory_fields_msg


def test_invalid_category_value():
    assert validate_from_json(invalid_category_value_data) == invalid_category_value_msg


def test_null_values():
    assert validate_from_json(null_values_data) == null_values_msg

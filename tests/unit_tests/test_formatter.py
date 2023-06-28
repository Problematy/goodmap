from goodmap.formatter import prepare_pin

test_place = {
    "name": "LASSO",
    "type_of_place": "container",
    "position": [51.113, 17.06],
    "random_field": "random_string",
    "types": ["shoes"],
    "gender": ["male", "female"],
    "dict_data": {"a": "b"},
    "plain_text": "text",
}


def test_formatting_when_missing_visible_field():
    visible_fields = ["types", "gender", "visible_without_data", "dict_data", "plain_text"]
    expected_data = {
        "title": "LASSO",
        "subtitle": "container",
        "position": [51.113, 17.06],
        "data": {
            "dict_data": {"a": "b"},
            "types": ["shoes"],
            "gender": ["male", "female"],
            "plain_text": "text",
        },
    }
    assert prepare_pin(test_place, visible_fields) == expected_data

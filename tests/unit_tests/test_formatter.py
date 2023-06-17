from goodmap.formatter import prepare_pin

test_place = {
    "name": "LASSO",
    "type_of_place": "container",
    "position": [51.113, 17.06],
    "random_field": "random_string",
    "types": ["shoes"],
    "gender": ["male", "female"]
}


def test_formatting_when_missing_visible_field():
    visible_fields = ["types", "gender", "visible_without_data"]
    expected_data = {
        "title": "LASSO",
        "subtitle": "container",
        "position": [51.113, 17.06],
        "data": {"types": ["shoes"], "gender": ["male", "female"]},
    }
    assert prepare_pin(test_place, visible_fields) == expected_data

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


def test_field_plugin_wraps_dict_value_with_scope():
    place = {**test_place, "promo_code": {"code": "SUMMER24", "text": "Get it", "color": "#f00"}}
    result = prepare_pin(place, ["promo_code"], [], field_plugins={"promo_code": "promocode"})
    assert result["data"] == [
        ["promo_code", {"scope": "promocode", "code": "U1VNTUVSMjQ=", "text": "Get it", "color": "#f00"}]
    ]


def test_field_plugin_ignores_non_dict_values():
    result = prepare_pin(test_place, ["plain_text"], [], field_plugins={"plain_text": "someplugin"})
    assert result["data"] == [["plain_text", "text"]]


def test_field_plugin_drops_unconfigured_dict_with_code():
    place = {**test_place, "promo_code": {"code": "HIDDEN"}}
    result = prepare_pin(place, ["promo_code"], [], field_plugins={})
    assert result["data"] == []


def test_formatting_when_missing_visible_field():
    visible_fields = ["types", "gender", "visible_without_data", "dict_data", "plain_text"]
    expected_data = {
        "title": "LASSO",
        "subtitle": "container",
        "position": [51.113, 17.06],
        "data": [
            ["types", ["shoes"]],
            ["gender", ["male", "female"]],
            ["dict_data", {"a": "b"}],
            ["plain_text", "text"],
        ],
        "metadata": {},
    }
    assert prepare_pin(test_place, visible_fields, []) == expected_data

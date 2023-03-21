from goodmap.formatter import prepare_pin, safe_gettext
from flask_babel import gettext
import pytest

test_place = {
            "name": "LASSO",
            "type_of_place": "container",
            "position": [51.113, 17.06],
            "random_field": "random_string",
            "types": ["shoes"],
            "gender": ["male", "female"]
        }


def test_formatting():
    visible_fields = ["types", "gender"]
    expected_data = {
        "title": "LASSO",
        "subtitle": "container",
        "position": [51.113, 17.06],
        "data": {
            "types": ["shoes"],
            "gender": ["male", "female"]
        }
    }
    assert prepare_pin(test_place, visible_fields) == expected_data


@pytest.mark.parametrize(
    ("arg", "expected"),
    (
        ([], []),
        (["abc"], [gettext("abc")]),
        ({}, {}),
        ({"a": "b"}, {"a": "b"}),
        ("abc", gettext("abc")),
    ),
)
def test_safe_gettext(arg: object, expected: object) -> None:
    assert safe_gettext(arg) == expected

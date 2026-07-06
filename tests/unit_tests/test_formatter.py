from platzky.shortcodes.shortcode import Shortcode, ShortcodeAttrs

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


class _FakeShortcode(Shortcode):
    """Minimal shortcode stub for formatter tests."""

    name = "promo_code"
    description = "test"

    def __init__(self, defaults=None):
        self._defaults = defaults or {}

    def transform_field_value(self, value: object) -> dict[str, object]:
        return {**self._defaults, "value": value, "type": self.name}

    def render(self, attrs: ShortcodeAttrs, content: str) -> str:
        return content


def test_field_plugin_transforms_value():
    place = {**test_place, "promo_code": "SAVE20"}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _FakeShortcode()})
    assert result["data"] == [["promo_code", {"type": "promo_code", "value": "SAVE20"}]]


def test_field_plugin_merges_defaults():
    place = {**test_place, "promo_code": "SAVE20"}
    sc = _FakeShortcode(defaults={"color": "#4caf50", "text": "Reveal"})
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": sc})
    assert result["data"] == [
        [
            "promo_code",
            {"type": "promo_code", "value": "SAVE20", "color": "#4caf50", "text": "Reveal"},
        ]
    ]


class _DefaultShortcode(Shortcode):
    """Shortcode relying on platzky's default transform_field_value (no override)."""

    name = "promo_code"
    description = "test"

    def render(self, attrs: ShortcodeAttrs, content: str) -> str:
        return content


def test_field_plugin_uses_platzky_default_type_key():
    """platzky's default transform_field_value emits the ``type`` key goodmap routes on.

    Guards the cross-repo contract: goodmap's frontend resolves field renderers by ``type``,
    so a plugin using platzky's default shortcode (no override) must land under ``type``.
    """
    place = {**test_place, "promo_code": {"code": "SAVE20"}}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _DefaultShortcode()})
    assert result["data"] == [["promo_code", {"type": "promo_code", "code": "SAVE20"}]]


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

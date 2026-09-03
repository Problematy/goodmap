from platzky.shortcodes.shortcode import Shortcode, ShortcodeAttr, ShortcodeAttrs

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
    content_key = "code"
    attributes = ShortcodeAttrs([ShortcodeAttr("color", "test")])

    def render(self, attrs: ShortcodeAttrs, content: str) -> str:
        return f"<b>{attrs.color}:{content}</b>"


def test_field_plugin_renders_the_value_as_html():
    """The shortcode renders its own field, so a plugin needs no frontend code here."""
    place = {**test_place, "promo_code": "SAVE20"}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _FakeShortcode()})
    assert result["data"] == [
        ["promo_code", {"type": "promo_code", "code": "SAVE20", "html": "<b>:SAVE20</b>"}]
    ]


def test_field_plugin_carries_entry_keys_for_a_react_renderer():
    """A field plugin rendering from the data gets the entry's own keys alongside."""
    place = {**test_place, "promo_code": {"code": "SAVE20", "color": "red"}}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _FakeShortcode()})
    assert result["data"] == [
        [
            "promo_code",
            {
                "type": "promo_code",
                "code": "SAVE20",
                "color": "red",
                "html": "<b>red:SAVE20</b>",
            },
        ]
    ]


def test_entry_cannot_redirect_its_field_at_another_renderer():
    place = {**test_place, "promo_code": {"code": "X", "type": "hyperlink"}}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _FakeShortcode()})
    assert result["data"] == [
        ["promo_code", {"type": "promo_code", "code": "X", "html": "<b>:X</b>"}]
    ]


class _DefaultShortcode(Shortcode):
    """Shortcode leaving ``content_key`` at its default."""

    name = "promo_code"
    description = "test"

    def render(self, attrs: ShortcodeAttrs, content: str) -> str:
        return content


def test_bare_value_lands_under_the_default_content_key():
    """Without a declared ``content_key`` a bare value is stored under ``content``."""
    place = {**test_place, "promo_code": "SAVE20"}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _DefaultShortcode()})
    assert result["data"] == [
        ["promo_code", {"type": "promo_code", "content": "SAVE20", "html": "SAVE20"}]
    ]


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

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


def test_hyperlink_field_is_rendered_server_side():
    """A built-in type named in the data is rendered here, so the frontend needs no component."""
    place = {**test_place, "website": {"type": "hyperlink", "value": "https://example.com"}}
    result = prepare_pin(place, ["website"], [])
    assert result["data"] == [
        [
            "website",
            {
                "type": "hyperlink",
                "value": "https://example.com",
                "html": (
                    '<a href="https://example.com" target="_blank" '
                    'rel="noopener noreferrer">https://example.com</a>'
                ),
            },
        ]
    ]


def test_hyperlink_uses_display_value_as_the_link_text():
    place = {
        **test_place,
        "website": {
            "type": "hyperlink",
            "value": "https://example.com",
            "displayValue": "Example",
        },
    }
    result = prepare_pin(place, ["website"], [])
    assert ">Example</a>" in result["data"][0][1]["html"]


def test_hyperlink_accepts_contact_schemes():
    """mailto:/tel: are how a place's contact details are written, and they navigate nowhere."""
    place = {**test_place, "email": {"type": "hyperlink", "value": "mailto:hi@example.com"}}
    result = prepare_pin(place, ["email"], [])
    assert result["data"][0][1]["html"] == (
        '<a href="mailto:hi@example.com">mailto:hi@example.com</a>'
    )


def test_hyperlink_with_a_refused_url_keeps_its_text_unlinked():
    """The label would otherwise sit above a blank, and the text is the part a reader wanted."""
    place = {
        **test_place,
        "website": {
            "type": "hyperlink",
            "value": "javascript:alert(1)",
            "displayValue": "<b>x</b>",
        },
    }
    result = prepare_pin(place, ["website"], [])
    assert result["data"][0][1]["html"] == "&lt;b&gt;x&lt;/b&gt;"


def test_cta_is_rendered_as_a_link_too():
    """CTA and hyperlink differ in presentation, not in what they are, so they share a renderer."""
    place = {
        **test_place,
        "CTA": {"type": "CTA", "value": "https://example.com", "displayValue": "Go"},
    }
    result = prepare_pin(place, ["CTA"], [])
    assert result["data"][0][1]["html"] == (
        '<a href="https://example.com" target="_blank" rel="noopener noreferrer">Go</a>'
    )


def test_cta_with_a_refused_url_keeps_its_text_unlinked():
    place = {
        **test_place,
        "CTA": {"type": "CTA", "value": "data:text/html,x", "displayValue": "Go"},
    }
    result = prepare_pin(place, ["CTA"], [])
    assert result["data"][0][1]["html"] == "Go"


def test_a_plugin_bound_field_is_not_reached_by_a_builtin_type():
    """The plugin owns its field outright; the data cannot redirect it at a built-in."""
    place = {**test_place, "promo_code": {"code": "X", "type": "hyperlink", "value": "https://e.x"}}
    result = prepare_pin(place, ["promo_code"], [], shortcodes={"promo_code": _FakeShortcode()})
    assert result["data"][0][1]["type"] == "promo_code"
    assert result["data"][0][1]["html"] == "<b>:X</b>"


def test_an_unknown_type_is_left_alone():
    place = {**test_place, "thing": {"type": "not_a_field_type", "value": "x"}}
    result = prepare_pin(place, ["thing"], [])
    assert result["data"] == [["thing", {"type": "not_a_field_type", "value": "x"}]]


def test_a_non_string_type_is_not_looked_up():
    """A stored ``type`` is data, and an unhashable one must not reach the registry lookup."""
    place = {**test_place, "thing": {"type": ["hyperlink"], "value": "x"}}
    result = prepare_pin(place, ["thing"], [])
    assert result["data"] == [["thing", {"type": ["hyperlink"], "value": "x"}]]


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

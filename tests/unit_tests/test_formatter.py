from collections.abc import Sequence
from typing import Any

import pytest
from markupsafe import Markup
from platzky.shortcodes.shortcode import Shortcode, ShortcodeAttr, ShortcodeAttrs

from goodmap.formatter import PinFormatter

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

    def render(self, attrs: ShortcodeAttrs, content: str, children: Sequence[Markup]) -> str:
        return f"<b>{attrs.color}:{content}</b>"


def test_field_plugin_renders_the_value_as_html():
    """The shortcode renders its own field, so a plugin needs no frontend code here."""
    place = {**test_place, "promo_code": "SAVE20"}
    result = PinFormatter(
        ["promo_code"],
        [],
        plugin_shortcodes={"promo_code": _FakeShortcode()},
    ).prepare_pin(place)
    assert result["data"] == [
        ["promo_code", {"type": "promo_code", "code": "SAVE20", "html": "<b>:SAVE20</b>"}]
    ]


def test_field_plugin_carries_entry_keys_for_a_react_renderer():
    """A field plugin rendering from the data gets the entry's own keys alongside."""
    place = {**test_place, "promo_code": {"code": "SAVE20", "color": "red"}}
    result = PinFormatter(
        ["promo_code"],
        [],
        plugin_shortcodes={"promo_code": _FakeShortcode()},
    ).prepare_pin(place)
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
    result = PinFormatter(
        ["promo_code"],
        [],
        plugin_shortcodes={"promo_code": _FakeShortcode()},
    ).prepare_pin(place)
    assert result["data"] == [
        ["promo_code", {"type": "promo_code", "code": "X", "html": "<b>:X</b>"}]
    ]


class _DefaultShortcode(Shortcode):
    """Shortcode leaving ``content_key`` at its default."""

    name = "promo_code"
    description = "test"

    def render(self, attrs: ShortcodeAttrs, content: str, children: Sequence[Markup]) -> str:
        return content


def test_hyperlink_field_is_rendered_server_side():
    """A built-in type named in the data is rendered here, so the frontend needs no component."""
    place = {**test_place, "website": {"type": "hyperlink", "value": "https://example.com"}}
    result = PinFormatter(["website"], []).prepare_pin(place)
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
    result = PinFormatter(["website"], []).prepare_pin(place)
    assert ">Example</a>" in result["data"][0][1]["html"]


def test_hyperlink_accepts_contact_schemes():
    """mailto:/tel: are how a place's contact details are written, and they navigate nowhere."""
    place = {**test_place, "email": {"type": "hyperlink", "value": "mailto:hi@example.com"}}
    result = PinFormatter(["email"], []).prepare_pin(place)
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
    result = PinFormatter(["website"], []).prepare_pin(place)
    assert result["data"][0][1]["html"] == "&lt;b&gt;x&lt;/b&gt;"


def test_cta_is_rendered_as_a_link_too():
    """CTA and hyperlink differ in presentation, not in what they are, so they share a renderer."""
    place = {
        **test_place,
        "CTA": {"type": "CTA", "value": "https://example.com", "displayValue": "Go"},
    }
    result = PinFormatter(["CTA"], []).prepare_pin(place)
    assert result["data"][0][1]["html"] == (
        '<a href="https://example.com" target="_blank" rel="noopener noreferrer">Go</a>'
    )


def test_cta_with_a_refused_url_keeps_its_text_unlinked():
    place = {
        **test_place,
        "CTA": {"type": "CTA", "value": "data:text/html,x", "displayValue": "Go"},
    }
    result = PinFormatter(["CTA"], []).prepare_pin(place)
    assert result["data"][0][1]["html"] == "Go"


def test_a_plugin_bound_field_is_not_reached_by_a_builtin_type():
    """The plugin owns its field outright; the data cannot redirect it at a built-in."""
    place = {**test_place, "promo_code": {"code": "X", "type": "hyperlink", "value": "https://e.x"}}
    result = PinFormatter(
        ["promo_code"],
        [],
        plugin_shortcodes={"promo_code": _FakeShortcode()},
    ).prepare_pin(place)
    assert result["data"][0][1]["type"] == "promo_code"
    assert result["data"][0][1]["html"] == "<b>:X</b>"


def test_an_unknown_type_is_left_alone():
    place = {**test_place, "thing": {"type": "not_a_field_type", "value": "x"}}
    result = PinFormatter(["thing"], []).prepare_pin(place)
    assert result["data"] == [["thing", {"type": "not_a_field_type", "value": "x"}]]


def test_a_non_string_type_is_not_looked_up():
    """A stored ``type`` is data, and an unhashable one must not reach the registry lookup."""
    place = {**test_place, "thing": {"type": ["hyperlink"], "value": "x"}}
    result = PinFormatter(["thing"], []).prepare_pin(place)
    assert result["data"] == [["thing", {"type": ["hyperlink"], "value": "x"}]]


def test_bare_value_lands_under_the_default_content_key():
    """Without a declared ``content_key`` a bare value is stored under ``content``."""
    place = {**test_place, "promo_code": "SAVE20"}
    result = PinFormatter(
        ["promo_code"],
        [],
        plugin_shortcodes={"promo_code": _DefaultShortcode()},
    ).prepare_pin(place)
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
    assert PinFormatter(visible_fields, []).prepare_pin(test_place) == expected_data


def test_a_field_whose_value_is_none_is_left_out():
    """``model_dump`` keeps an unset optional field as None; a label over nothing says nothing."""
    place = {**test_place, "remark": None}
    data = PinFormatter(["remark", "plain_text"], []).prepare_pin(place)["data"]
    assert data == [["plain_text", "text"]]


def test_html_in_the_data_is_dropped_rather_than_rendered_as_markup():
    """``html`` means "the server rendered this", and the popup injects it as markup.

    A location entry can carry any key - LocationBase allows extras, and a suggested or
    imported point is not goodmap's own output - so an ``html`` nothing rendered has to be
    stripped rather than passed on to be injected.
    """
    place = {**test_place, "evil": {"html": "<img src=x onerror=alert(1)>", "value": "hi"}}
    result = PinFormatter(["evil"], []).prepare_pin(place)
    assert result["data"] == [["evil", {"value": "hi"}]]


def test_a_rendered_field_still_gets_its_html():
    """The guard above must not disturb a field something actually rendered."""
    place = {**test_place, "website": {"type": "hyperlink", "value": "https://example.com"}}
    assert "html" in PinFormatter(["website"], []).prepare_pin(place)["data"][0][1]


@pytest.mark.parametrize("display_value", ["", None], ids=["empty", "null"])
def test_a_blank_display_value_falls_back_to_the_url(display_value):
    """An anchor with no text is invisible and unclickable, and leaves the field's label
    sitting above nothing - so a blank displayValue reads as absent, not as empty text."""
    place = {
        **test_place,
        "website": {
            "type": "hyperlink",
            "value": "https://example.com",
            "displayValue": display_value,
        },
    }
    result = PinFormatter(["website"], []).prepare_pin(place)
    assert ">https://example.com</a>" in result["data"][0][1]["html"]


def _photo_entries(**image: Any) -> list[Any]:
    """The popup's entries for a place whose only visible field is a ``photo`` image."""
    place = {**test_place, "photo": {"type": "image", **image}}
    return PinFormatter(["photo"], []).prepare_pin(place)["data"]


def _render_photo(**image: Any) -> dict[str, Any]:
    """The popup value of a ``photo`` image field that was shown."""
    ((_, value),) = _photo_entries(**image)
    return value


def test_image_is_rendered_with_its_own_alt():
    value = _render_photo(url="https://example.com/1.jpg", alt="The deck")
    assert value["type"] == "image"
    assert value["html"] == '<img src="https://example.com/1.jpg" alt="The deck">'


def test_image_without_an_alt_gets_an_empty_one():
    """Without a description of its own, an image is treated as decorative."""
    html = _render_photo(url="https://example.com/1.jpg")["html"]
    assert html == '<img src="https://example.com/1.jpg" alt="">'


def test_image_html_from_the_data_is_not_passed_on():
    html = _render_photo(url="https://example.com/1.jpg", html="<script>x</script>")["html"]
    assert "<script>" not in html


def test_image_passes_width_and_height_through():
    html = _render_photo(url="https://example.com/1.jpg", width=400, height=300)["html"]
    assert html == '<img src="https://example.com/1.jpg" alt="" width="400" height="300">'


def test_image_on_a_site_path_is_accepted():
    assert _render_photo(url="/static/1.jpg")["html"] == '<img src="/static/1.jpg" alt="">'


@pytest.mark.parametrize(
    "image",
    [
        {"url": "javascript:alert(1)"},
        {"url": "data:image/png;base64,AAAA"},
        {"url": "http://example.com/1.jpg"},
        {"alt": "no url"},
        {"url": "https://example.com/1.jpg", "width": "wide"},
        {"items": [{"url": "https://example.com/1.jpg"}]},  # one image per field
    ],
)
def test_refused_image_leaves_the_field_out(image):
    """A label over a blank says nothing; the popup does not need to know why."""
    assert _photo_entries(**image) == []


def test_platzky_builtins_outside_the_allowlist_are_not_rendered():
    """``html`` would hand data nobody vouched for raw markup in the popup."""
    place = {**test_place, "evil": {"type": "html", "html": "<b>x</b>"}}
    value = PinFormatter(["evil"], []).prepare_pin(place)["data"][0][1]
    assert value == {"type": "html"}

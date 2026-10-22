import logging
from collections.abc import Sequence

import pytest
from markupsafe import Markup
from platzky.shortcodes.shortcode import Shortcode, ShortcodeAttr, ShortcodeAttrs

from goodmap.alt_template import DEFAULT_ALT_TEMPLATE, AltTemplate
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

    def render(self, attrs: ShortcodeAttrs, content: str, children: Sequence[Markup]) -> str:
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

    def render(self, attrs: ShortcodeAttrs, content: str, children: Sequence[Markup]) -> str:
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


def test_html_in_the_data_is_dropped_rather_than_rendered_as_markup():
    """``html`` means "the server rendered this", and the popup injects it as markup.

    A location entry can carry any key - LocationBase allows extras, and a suggested or
    imported point is not goodmap's own output - so an ``html`` nothing rendered has to be
    stripped rather than passed on to be injected.
    """
    place = {**test_place, "evil": {"html": "<img src=x onerror=alert(1)>", "value": "hi"}}
    result = prepare_pin(place, ["evil"], [])
    assert result["data"] == [["evil", {"value": "hi"}]]


def test_a_rendered_field_still_gets_its_html():
    """The guard above must not disturb a field something actually rendered."""
    place = {**test_place, "website": {"type": "hyperlink", "value": "https://example.com"}}
    assert "html" in prepare_pin(place, ["website"], [])["data"][0][1]


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
    result = prepare_pin(place, ["website"], [])
    assert ">https://example.com</a>" in result["data"][0][1]["html"]


def _images(*items):
    return {**test_place, "images": {"type": "image", "items": list(items)}}


def test_image_items_are_each_rendered_and_joined():
    """The field's ``html`` joins the items' renderings; the items stay plain data."""
    place = _images({"url": "https://example.com/1.jpg"}, {"url": "https://example.com/2.jpg"})
    value = prepare_pin(place, ["images"], [])["data"][0][1]
    assert value["type"] == "image"
    assert value["html"] == (
        '<img src="https://example.com/1.jpg" alt="LASSO">'
        '<img src="https://example.com/2.jpg" alt="LASSO">'
    )
    assert value["items"] == [
        {"url": "https://example.com/1.jpg", "alt": "LASSO"},
        {"url": "https://example.com/2.jpg", "alt": "LASSO"},
    ]


def test_image_items_html_from_the_data_is_not_passed_on():
    place = _images({"url": "https://example.com/1.jpg", "html": "<script>x</script>"})
    value = prepare_pin(place, ["images"], [])["data"][0][1]
    assert "html" not in value["items"][0]
    assert "<script>" not in value["html"]


def test_image_passes_width_and_height_through():
    place = _images({"url": "https://example.com/1.jpg", "width": 400, "height": 300})
    html = prepare_pin(place, ["images"], [])["data"][0][1]["html"]
    assert html == '<img src="https://example.com/1.jpg" alt="LASSO" width="400" height="300">'


@pytest.mark.parametrize(
    "item",
    [
        {"url": "javascript:alert(1)"},
        {"url": "data:image/png;base64,AAAA"},
        {"url": "http://example.com/1.jpg"},
        {"alt": "no url"},
        {"url": "https://example.com/1.jpg", "width": "wide"},
    ],
)
def test_refused_image_item_is_dropped(item):
    place = _images(item, {"url": "https://example.com/ok.jpg"})
    value = prepare_pin(place, ["images"], [])["data"][0][1]
    assert [i["url"] for i in value["items"]] == ["https://example.com/ok.jpg"]
    assert value["html"] == '<img src="https://example.com/ok.jpg" alt="LASSO">'


def test_image_on_a_site_path_is_accepted():
    html = prepare_pin(_images({"url": "/static/1.jpg"}), ["images"], [])["data"][0][1]["html"]
    assert html == '<img src="/static/1.jpg" alt="LASSO">'


def test_image_item_that_is_not_an_object_is_dropped_with_a_warning(caplog):
    place = _images("https://example.com/bare.jpg", {"url": "https://example.com/ok.jpg"})
    with caplog.at_level(logging.WARNING):
        value = prepare_pin(place, ["images"], [])["data"][0][1]
    assert [i["url"] for i in value["items"]] == ["https://example.com/ok.jpg"]
    assert "{'url': ...}" in caplog.text


@pytest.mark.parametrize("field_type", ["hyperlink", "CTA"])
def test_items_on_a_type_other_than_image_render_nothing(field_type, caplog):
    """Only images hold several values; anything else with items is left out, and says why."""
    place = {
        **test_place,
        "links": {"type": field_type, "items": [{"value": "https://a.org"}]},
    }
    with caplog.at_level(logging.WARNING):
        assert prepare_pin(place, ["links"], [])["data"] == []
    assert "items is for images" in caplog.text


def test_image_field_with_every_item_refused_is_left_out():
    """A label over a blank says nothing; the popup does not need to know why."""
    place = _images({"url": "javascript:alert(1)"})
    assert prepare_pin(place, ["images"], [])["data"] == []


def test_image_alt_defaults_to_the_template_and_an_items_own_alt_wins():
    place = _images(
        {"url": "https://example.com/1.jpg"},
        {"url": "https://example.com/2.jpg", "alt": "Own"},
        {"url": "https://example.com/3.jpg", "alt": ""},
    )
    template = AltTemplate("{{ type_of_place }} {{ name }}")
    items = prepare_pin(place, ["images"], [], alt_template=template)["data"][0][1]["items"]
    assert [item["alt"] for item in items] == ["container LASSO", "Own", ""]


def test_alt_default_is_not_given_to_a_type_without_alt():
    place = {**test_place, "website": {"type": "hyperlink", "value": "https://example.com"}}
    value = prepare_pin(place, ["website"], [], alt_template=AltTemplate(DEFAULT_ALT_TEMPLATE))
    assert "alt" not in value["data"][0][1]


def test_platzky_builtins_outside_the_allowlist_are_not_rendered():
    """``html`` would hand data nobody vouched for raw markup in the popup."""
    place = {
        **test_place,
        "evil": {"type": "html", "html": "<b>x</b>", "items": [{"html": "<script>x</script>"}]},
    }
    value = prepare_pin(place, ["evil"], [])["data"][0][1]
    assert value == {"type": "html", "items": [{}]}


def test_alt_template_translates_the_fields_it_wraps_in_underscore(monkeypatch):
    def translate(text: str) -> str:
        return f"{text}-pl"

    monkeypatch.setattr("goodmap.translation.gettext", translate)
    template = AltTemplate("{{ _(type_of_place) }} {{ _(types) | join(',') }} {{ name }}")
    place = _images({"url": "https://example.com/1.jpg"})
    items = prepare_pin(place, ["images"], [], alt_template=template)["data"][0][1]["items"]
    assert items[0]["alt"] == "container-pl shoes-pl LASSO"


def test_alt_template_compares_stored_values(monkeypatch):
    """A translated value differs per language; the stored one the template sees does not."""

    def gettext(text: str) -> str:
        return {"true": "tak"}.get(text, text)

    monkeypatch.setattr("goodmap.translation.gettext", gettext)
    template = AltTemplate("{{ 'free' if is_free == 'true' else 'paid' }} {{ _(is_free) }}")
    place = {**_images({"url": "https://example.com/1.jpg"}), "is_free": "true"}
    items = prepare_pin(place, ["images"], [], alt_template=template)["data"][0][1]["items"]
    assert items[0]["alt"] == "free tak"


def test_alt_template_empty_field_prints_nothing(monkeypatch):
    """``gettext("")`` is the catalogue's header, which a screen reader would read out."""

    def gettext(text: str) -> str:
        return text or "HEADER"

    monkeypatch.setattr("goodmap.translation.gettext", gettext)
    template = AltTemplate("{{ name }} {{ _(remark) }}")
    place = {**_images({"url": "https://example.com/1.jpg"}), "remark": ""}
    items = prepare_pin(place, ["images"], [], alt_template=template)["data"][0][1]["items"]
    assert items[0]["alt"] == "LASSO"


def test_alt_template_translates_only_what_it_wraps(monkeypatch):
    translated: list[object] = []

    def gettext(text: str) -> str:
        translated.append(text)
        return text

    monkeypatch.setattr("goodmap.translation.gettext", gettext)
    place = _images({"url": "https://example.com/1.jpg"})
    prepare_pin(place, [], [])  # nothing visible: only the alt could translate anything
    translated.clear()
    prepare_pin(place, ["images"], [], alt_template=AltTemplate("{{ _(name) }}"))
    assert "random_string" not in translated
    assert "LASSO" in translated


def test_image_alt_null_counts_as_absent():
    """Imported data writing ``"alt": null`` means "not given", not "decorative"."""
    place = _images({"url": "https://example.com/1.jpg", "alt": None})
    template = AltTemplate(DEFAULT_ALT_TEMPLATE)
    items = prepare_pin(place, ["images"], [], alt_template=template)["data"][0][1]["items"]
    assert items[0]["alt"] == "LASSO"


def test_alt_template_is_not_rendered_for_a_pin_without_images(monkeypatch):
    calls: list[tuple[object, ...]] = []

    def render(*args: object) -> str:
        calls.append(args)
        return ""

    monkeypatch.setattr(AltTemplate, "render", render)
    place = {**test_place, "website": {"type": "hyperlink", "value": "https://example.com"}}
    prepare_pin(
        place,
        ["website", "plain_text"],
        [],
        alt_template=AltTemplate(DEFAULT_ALT_TEMPLATE),
    )
    assert calls == []


def test_alt_template_is_rendered_once_per_pin(monkeypatch):
    calls: list[tuple[object, ...]] = []

    def render(*args: object) -> str:
        calls.append(args)
        return "x"

    monkeypatch.setattr(AltTemplate, "render", render)
    place = {
        **_images({"url": "https://example.com/1.jpg"}, {"url": "https://example.com/2.jpg"}),
        "more": {"type": "image", "items": [{"url": "https://example.com/3.jpg"}]},
    }
    prepare_pin(place, ["images", "more"], [], alt_template=AltTemplate(DEFAULT_ALT_TEMPLATE))
    assert len(calls) == 1


class _AltShortcode(_FakeShortcode):
    attributes = ShortcodeAttrs([ShortcodeAttr("alt", "test")])

    def render(self, attrs: ShortcodeAttrs, content: str, children: Sequence[Markup]) -> str:
        return f"<i>{attrs.alt}:{content}</i>"


def test_plugin_field_keeps_its_own_rendering():
    """``items`` and place-derived defaults are for goodmap's own types only."""
    place = {**test_place, "promo_code": {"code": "X", "items": [{"code": "Y"}]}}
    value = prepare_pin(
        place,
        ["promo_code"],
        [],
        shortcodes={"promo_code": _AltShortcode()},
        alt_template=AltTemplate(DEFAULT_ALT_TEMPLATE),
    )["data"][0][1]
    assert value["html"] == "<i>:X</i>"
    assert value["items"] == [{"code": "Y"}]

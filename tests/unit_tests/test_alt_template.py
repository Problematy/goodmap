import logging

import pytest
from jinja2 import TemplateSyntaxError

from goodmap.alt_template import compile_alt_template, render_alt

place = {
    "name": "Grunwaldzki",
    "type_of_place": "big bridge",
    "is_free": "true",
    "amenities": ["lighting", "benches"],
}


def test_default_describes_the_place_by_its_name():
    assert render_alt(compile_alt_template(None), place) == "Grunwaldzki"


@pytest.mark.parametrize(("is_free", "expected"), [("true", "free"), ("false", "paid")])
def test_conditional(is_free, expected):
    template = compile_alt_template("{{ 'free' if is_free == 'true' else 'paid' }}")
    assert render_alt(template, {**place, "is_free": is_free}) == expected


def test_lists_are_joined_by_the_template():
    template = compile_alt_template("{{ amenities | join(', ') }}")
    assert render_alt(template, place) == "lighting, benches"


def test_missing_field_prints_empty_and_whitespace_collapses():
    template = compile_alt_template("photo of\n  {{ speed_limit }}   {{ type_of_place }} ")
    assert render_alt(template, place) == "photo of big bridge"


def test_template_text_can_be_translated(monkeypatch):
    def translate(text: str) -> str:
        return f"{text}-pl"

    template = compile_alt_template("{{ _('photo of') }} {{ name }}")
    monkeypatch.setitem(template.environment.globals, "_", translate)
    assert render_alt(template, place) == "photo of-pl Grunwaldzki"


def test_syntax_error_raises_at_compile_time():
    with pytest.raises(TemplateSyntaxError):
        compile_alt_template("{{ name")


def test_sandbox_refusal_falls_back_to_the_name(caplog):
    template = compile_alt_template("{{ name.__class__.__mro__ }}")
    with caplog.at_level(logging.WARNING):
        assert render_alt(template, place) == "Grunwaldzki"
    assert "IMAGE_ALT_TEMPLATE" in caplog.text


def test_none_prints_as_nothing():
    """``model_dump`` keeps an unset optional field as None, which Jinja would print."""
    template = compile_alt_template("{{ name }} {{ remark }}")
    assert render_alt(template, {**place, "remark": None}) == "Grunwaldzki"


def test_any_render_error_falls_back_to_the_name():
    template = compile_alt_template("{{ name }} {{ 100 // capacity }}")
    assert render_alt(template, {**place, "capacity": 0}) == "Grunwaldzki"

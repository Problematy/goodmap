import logging

import flask_babel
import pytest
from jinja2 import TemplateSyntaxError

from goodmap.alt_template import DEFAULT_ALT_TEMPLATE, AltTemplate

place = {
    "name": "Grunwaldzki",
    "type_of_place": "big bridge",
    "is_free": "true",
    "amenities": ["lighting", "benches"],
}


def test_default_describes_the_place_by_its_name():
    assert AltTemplate(DEFAULT_ALT_TEMPLATE).render(place) == "Grunwaldzki"


@pytest.mark.parametrize(("is_free", "expected"), [("true", "free"), ("false", "paid")])
def test_conditional(is_free, expected):
    template = AltTemplate("{{ 'free' if is_free == 'true' else 'paid' }}")
    assert template.render({**place, "is_free": is_free}) == expected


def test_lists_are_joined_by_the_template():
    template = AltTemplate("{{ amenities | join(', ') }}")
    assert template.render(place) == "lighting, benches"


def test_missing_field_prints_empty_and_whitespace_collapses():
    template = AltTemplate("photo of\n  {{ speed_limit }}   {{ type_of_place }} ")
    assert template.render(place) == "photo of big bridge"


_POLISH = {"photo of": "zdjęcie", "photo of %(name)s": "zdjęcie: %(name)s"}


def _to_polish(_domain: object, text: str, **variables: object) -> str:
    return _POLISH.get(text, text) % variables


def test_template_text_can_be_translated(monkeypatch):
    # flask_babel's gettext hands each call to the active Domain, so this reaches ``_()``.
    monkeypatch.setattr(flask_babel.Domain, "gettext", _to_polish)
    template = AltTemplate("{{ _('photo of') }} {{ name }}")
    assert template.render(place) == "zdjęcie Grunwaldzki"


def test_template_text_takes_formatting_arguments(monkeypatch):
    monkeypatch.setattr(flask_babel.Domain, "gettext", _to_polish)
    template = AltTemplate("{{ _('photo of %(name)s', name=name) }}")
    assert template.render(place) == "zdjęcie: Grunwaldzki"


def test_syntax_error_raises_at_compile_time():
    with pytest.raises(TemplateSyntaxError):
        AltTemplate("{{ name")


def test_sandbox_refusal_falls_back_to_the_name(caplog):
    template = AltTemplate("{{ name.__class__.__mro__ }}")
    with caplog.at_level(logging.WARNING):
        assert template.render(place) == "Grunwaldzki"
    assert "IMAGE_ALT_TEMPLATE" in caplog.text


def test_none_prints_as_nothing():
    """``model_dump`` keeps an unset optional field as None, which Jinja would print."""
    template = AltTemplate("{{ name }} {{ remark }}")
    assert template.render({**place, "remark": None}) == "Grunwaldzki"


def test_any_render_error_falls_back_to_the_name():
    template = AltTemplate("{{ name }} {{ 100 // capacity }}")
    assert template.render({**place, "capacity": 0}) == "Grunwaldzki"

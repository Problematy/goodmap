"""The default ``alt`` text for a marker image, built from the place it belongs to.

An image item may carry its own ``alt``; most will not, and an image with no description is
invisible to a screen reader. So the operator writes one template, ``IMAGE_ALT_TEMPLATE``,
and every image without its own ``alt`` gets that template rendered against its place.

The template is Jinja, which the operator already knows and Flask already ships, run in the
immutable sandbox so a template can reach the place's values and nothing behind them. It
is compiled once at startup - a syntax error fails the boot, not every popup - and rendered
per pin with the place's fields, as stored, as its context. What should be translated, the
template wraps in ``_()``: its own text and field values alike.
"""

import logging
from collections.abc import Mapping
from typing import Any

from flask_babel import gettext
from jinja2.sandbox import ImmutableSandboxedEnvironment

from goodmap.translation import safe_gettext

logger = logging.getLogger(__name__)

#: Used when the operator sets no template: every location has a name.
DEFAULT_ALT_TEMPLATE = "{{ name }}"


def _finalize(value: object) -> object:
    """Print None as nothing.

    ``model_dump`` keeps an unset optional field as None, and a screen reader would
    otherwise read out "None". With ``remark`` unset::

        {{ name }} {{ remark }}   ->  "Grunwaldzki"   (not "Grunwaldzki None")
    """
    return "" if value is None else value


# No autoescape: the result is an attribute value, and the image shortcode escapes it
# where it interpolates it. Escaping here as well would show ``&amp;`` in the alt.
_environment = ImmutableSandboxedEnvironment(autoescape=False, finalize=_finalize)


def _translate(*args: Any, **kwargs: Any) -> Any:
    """The template's ``_()``: translate text - the template's own or a field's - or a list.

    In a Polish request::

        {{ _('free') }}                         ->  "bezpłatny"
        {{ _(type_of_place) }}                  ->  "duży most"
        {{ _(amenities) | join(', ') }}         ->  "oświetlenie, ławki"
        {{ _('a %(kind)s', kind=_(type_of_place)) }}

    Formatting arguments go to ``gettext``; a value alone goes through ``safe_gettext``,
    which also takes a list, and leaves an empty field empty rather than looking it up.
    """
    if kwargs:
        return gettext(*args, **kwargs)
    return safe_gettext(*args)


_environment.globals["_"] = _translate


class AltTemplate:
    """A compiled alt template, which renders the alt text for one place at a time.

    The template sees the place's fields as stored, so a comparison holds in every
    language, and translates with ``_()`` what it prints. Example - a sentence with the
    name inside it, a translated field, a condition, and a clause only some places have::

        {{ _('Photo of %(name)s', name=name) }} ({{ _(type_of_place) }}):
        {{ _('free') if is_free == 'true' else _('paid') }}
        {%- if speed_limit %}, {{ _('speed limit %(limit)s km/h', limit=speed_limit) }}{% endif %}

    For ``{"name": "Grunwaldzki", "type_of_place": "big bridge", "is_free": "true",
    "speed_limit": "50"}`` that renders, in English and in a Polish request::

        Photo of Grunwaldzki (big bridge): free, speed limit 50 km/h
        Zdjęcie - Grunwaldzki (duży most): bezpłatny, ograniczenie prędkości 50 km/h

    and without a ``speed_limit``, just ``Photo of Grunwaldzki (big bridge): free``.

    * ``_('Photo of %(name)s', name=name)`` translates the whole phrase, so a language can
      put the name where its grammar wants it.
    * ``{{ _(type_of_place) }}`` translates the field: ``big bridge`` became ``duży most``.
      Without ``_()`` it would print ``big bridge`` in any language.
    * ``is_free == 'true'`` compares the stored value, so it holds in every language.
    * ``{%- if speed_limit %}`` leaves the clause out for a place without one, and its
      ``-`` keeps the comma against the word before it.
    """

    def __init__(self, template: str) -> None:
        """Compile the template.

        Args:
            template: The template text - the ``IMAGE_ALT_TEMPLATE`` config value, which
                defaults to :data:`DEFAULT_ALT_TEMPLATE`.

        Raises:
            jinja2.TemplateSyntaxError: If the template does not parse.
        """
        self._template = _environment.from_string(template)

    def render(self, place: Mapping[str, Any]) -> str:
        """Render the alt text for one place.

        A template that parsed can still fail on a particular place - the sandbox refusing
        an attribute, a filter given the wrong type, a division by a field that is zero -
        and a popup is not worth losing over its alt text, so any failure falls back to the
        place's name::

            alt = AltTemplate("{{ 100 // capacity }} people fit here")
            alt.render({"name": "Grunwaldzki", "capacity": 0})
            # 100 // 0 raises ZeroDivisionError, so: "Grunwaldzki", and a warning in the log

        Runs of whitespace collapse, so a template may be laid out over several lines::

            "photo of\n   {{ name }}  "   ->  "photo of Grunwaldzki"

        Args:
            place: The place's fields, as stored.

        Returns:
            The alt text, with whitespace runs collapsed.
        """
        try:
            rendered = self._template.render(place)
        except Exception:  # whatever the template raised, the popup still opens
            logger.warning(
                "IMAGE_ALT_TEMPLATE failed for a location; using its name.", exc_info=True
            )
            rendered = str(place.get("name", ""))
        return " ".join(rendered.split())

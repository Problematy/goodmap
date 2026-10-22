"""The default ``alt`` text for a marker image, built from the place it belongs to.

An image item may carry its own ``alt``; most will not, and an image with no description is
invisible to a screen reader. So the operator writes one template, ``IMAGE_ALT_TEMPLATE``,
and every image without its own ``alt`` gets that template rendered against its place.

The template is Jinja, which the operator already knows and Flask already ships, run in the
immutable sandbox so a template can reach the place's values and nothing behind them. It
is compiled once at startup - a syntax error fails the boot, not every popup - and rendered
per pin with the place's fields, already translated, as its context. A translated value is
the wrong thing to compare against - ``is_free`` reads ``tak`` in Polish - so the stored
values are there too, untranslated, as ``raw``.
"""

import logging
from collections.abc import Mapping
from typing import Any

from flask_babel import gettext
from jinja2 import meta
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


def _translate(*args: Any, **kwargs: Any) -> str:
    """The template's ``_()``, for translating the template's own text: ``gettext``.

    Formatting arguments work as in ``gettext``. In a Polish request, given a catalogue
    that translates the message::

        {{ _('photo of') }} {{ name }}                 ->  "zdjęcie Grunwaldzki"
        {{ _('photo of %(name)s', name=name) }}        ->  "zdjęcie Grunwaldzki"

    Looked up per call rather than bound once, so the ``gettext`` in effect is the one used.
    """
    return gettext(*args, **kwargs)


_environment.globals["_"] = _translate


class AltTemplate:
    """A compiled alt template, which renders the alt text for one place at a time.

    Example, in a Polish request whose catalogue translates these values::

        place = {"name": "Grunwaldzki", "type_of_place": "big bridge", "is_free": "true",
                 "amenities": ["lighting", "benches"]}

        AltTemplate("{{ name }}").render(place)                     # "Grunwaldzki"
        AltTemplate("{{ type_of_place }}").render(place)            # "duży most"
        AltTemplate("{{ amenities | join(', ') }}").render(place)   # "oświetlenie, ławki"
        AltTemplate("{{ 'free' if raw.is_free == 'true' else 'paid' }}").render(place)
                                                                    # "free"
        AltTemplate("{{ 'free' if is_free == 'true' else 'paid' }}").render(place)
                                                    # "paid" - is_free reads "tak" here
    """

    def __init__(self, source: str) -> None:
        """Compile the template.

        Args:
            source: The template - the ``IMAGE_ALT_TEMPLATE`` config value, which defaults to
                :data:`DEFAULT_ALT_TEMPLATE`.

        Raises:
            jinja2.TemplateSyntaxError: If the template does not parse.
        """
        parsed = _environment.parse(source)
        self._template = _environment.from_string(parsed)
        # The names it reads, so only those of a place's fields need translating.
        self._names = frozenset(meta.find_undeclared_variables(parsed))

    def render(self, place: Mapping[str, Any]) -> str:
        """Render the alt text for one place.

        A template that parsed can still fail on a particular place - the sandbox refusing
        an attribute, a filter given the wrong type, a division by a field that is zero -
        and a popup is not worth losing over its alt text, so any failure falls back to the
        place's name::

            AltTemplate("{{ 100 // capacity }}").render({"name": "LASSO", "capacity": 0})
            # "LASSO", and a warning in the log

        Runs of whitespace collapse, so a template may be laid out over several lines::

            "photo of\n   {{ name }}  "   ->  "photo of Grunwaldzki"

        Args:
            place: The place's fields, as stored. Those the template reads are translated
                into the request's language; ``raw`` keeps them as stored.

        Returns:
            The alt text, with whitespace runs collapsed.
        """
        # A field that is itself called ``raw`` keeps its name; the stored values are then
        # out of the template's reach, which beats renaming a field the operator chose.
        context = {
            "raw": place,
            **{name: safe_gettext(place[name]) for name in self._names if name in place},
        }
        try:
            rendered = self._template.render(context)
        except Exception:  # whatever the template raised, the popup still opens
            logger.warning(
                "IMAGE_ALT_TEMPLATE failed for a location; using its name.", exc_info=True
            )
            rendered = str(place.get("name", ""))
        return " ".join(rendered.split())

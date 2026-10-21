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
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from flask_babel import gettext
from jinja2 import Template, meta
from jinja2.sandbox import ImmutableSandboxedEnvironment

logger = logging.getLogger(__name__)

#: Used when the operator sets no template: every location has a name.
DEFAULT_ALT_TEMPLATE = "{{ name }}"


# No autoescape: the result is an attribute value, and the image shortcode escapes it
# where it interpolates it. Escaping here as well would show ``&amp;`` in the alt.
# ``finalize`` prints None as nothing: ``model_dump`` keeps an unset optional field as None,
# and a screen reader would otherwise read out "None".
def _finalize(value: object) -> object:
    return "" if value is None else value


_environment = ImmutableSandboxedEnvironment(autoescape=False, finalize=_finalize)
_environment.globals["_"] = gettext

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class AltTemplate:
    """A compiled alt template, and the names it reads, so only those need translating."""

    template: Template
    names: frozenset[str]


def compile_alt_template(source: str) -> AltTemplate:
    """Compile an alt template.

    Args:
        source: The template - the ``IMAGE_ALT_TEMPLATE`` config value, which defaults to
            :data:`DEFAULT_ALT_TEMPLATE`.

    Returns:
        The compiled template.

    Raises:
        jinja2.TemplateSyntaxError: If the template does not parse.
    """
    names = meta.find_undeclared_variables(_environment.parse(source))
    return AltTemplate(_environment.from_string(source), frozenset(names))


def _untranslated(value: Any) -> Any:
    return value


def render_alt(
    alt: AltTemplate, place: Mapping[str, Any], translate: Callable[[Any], Any] = _untranslated
) -> str:
    """Render the alt text for one place.

    A template that parsed can still fail on a particular place - the sandbox refusing an
    attribute, a filter given the wrong type, a division by a field that is zero - and a
    popup is not worth losing over its alt text, so any failure falls back to the place's
    name.

    Args:
        alt: From :func:`compile_alt_template`.
        place: The place's fields, as stored.
        translate: Applied to each field the template reads; ``raw`` is left as stored.

    Returns:
        The alt text, with whitespace runs collapsed.
    """
    # A field that is itself called ``raw`` keeps its name; the stored values are then out
    # of the template's reach, which beats renaming a field the operator chose.
    context = {"raw": place}
    context.update({name: translate(place[name]) for name in alt.names if name in place})
    try:
        rendered = alt.template.render(context)
    except Exception:  # whatever the template raised, the popup still opens
        logger.warning("IMAGE_ALT_TEMPLATE failed for a location; using its name.", exc_info=True)
        rendered = str(place.get("name", ""))
    return _WHITESPACE.sub(" ", rendered).strip()

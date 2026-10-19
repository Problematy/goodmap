"""The default ``alt`` text for a marker image, built from the place it belongs to.

An image item may carry its own ``alt``; most will not, and an image with no description is
invisible to a screen reader. So the operator writes one template, ``IMAGE_ALT_TEMPLATE``,
and every image without its own ``alt`` gets that template rendered against its place.

The template is Jinja, which the operator already knows and Flask already ships, run in the
immutable sandbox so a template can reach the place's values and nothing behind them. It
is compiled once at startup - a syntax error fails the boot, not every popup - and rendered
per pin with the place's fields, already translated, as its context.
"""

import logging
import re
from collections.abc import Mapping
from typing import Any

from flask_babel import gettext
from jinja2 import Template
from jinja2.sandbox import ImmutableSandboxedEnvironment

logger = logging.getLogger(__name__)

#: Used when the operator sets no template: every location has a name.
DEFAULT_ALT_TEMPLATE = "{{ name }}"

# No autoescape: the result is an attribute value, and the image shortcode escapes it
# where it interpolates it. Escaping here as well would show ``&amp;`` in the alt.
# ``finalize`` prints None as nothing: ``model_dump`` keeps an unset optional field as None,
# and a screen reader would otherwise read out "None".
_environment = ImmutableSandboxedEnvironment(
    autoescape=False, finalize=lambda value: "" if value is None else value
)
_environment.globals["_"] = gettext

_WHITESPACE = re.compile(r"\s+")


def compile_alt_template(source: str | None) -> Template:
    """Compile the operator's alt template, or the default when there is none.

    Args:
        source: The ``IMAGE_ALT_TEMPLATE`` config value.

    Returns:
        The compiled template.

    Raises:
        jinja2.TemplateSyntaxError: If the template does not parse.
    """
    return _environment.from_string(source or DEFAULT_ALT_TEMPLATE)


def render_alt(template: Template, context: Mapping[str, Any]) -> str:
    """Render the alt text for one place.

    A template that parsed can still fail on a particular place - the sandbox refusing an
    attribute, a filter given the wrong type, a division by a field that is zero - and a
    popup is not worth losing over its alt text, so any failure falls back to the place's
    name.

    Args:
        template: From :func:`compile_alt_template`.
        context: The place's fields, already translated.

    Returns:
        The alt text, with whitespace runs collapsed.
    """
    try:
        rendered = template.render(context)
    except Exception:  # whatever the template raised, the popup still opens
        logger.warning("IMAGE_ALT_TEMPLATE failed for a location; using its name.", exc_info=True)
        rendered = str(context.get("name", ""))
    return _WHITESPACE.sub(" ", rendered).strip()

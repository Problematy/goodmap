"""Formatters for translating and preparing location data for display."""

import logging
from typing import Any

from flask_babel import gettext, lazy_gettext

from goodmap.field_types import BUILTIN_FIELD_TYPES

logger = logging.getLogger(__name__)


def safe_gettext(text):
    """Translate ``text``, mapping over a list and leaving a dict alone.

    Args:
        text: A str, a list of str, or a dict.

    Returns:
        The translation, in the same shape as the input.
    """
    if isinstance(text, list):
        return list(map(gettext, text))
    elif isinstance(text, dict):
        return text
    else:
        return gettext(text)


def _builtin_shortcode(value):
    """The built-in shortcode a field's own data asks for, if any.

    Reached only where no plugin shortcode claimed the field by name, and only the closed
    catalogue in :mod:`goodmap.field_types` is on offer - so an entry can never name its way
    to a plugin's renderer.

    Args:
        value: The field's value from the location data.

    Returns:
        The Shortcode for the declared ``type``, or None when it names none goodmap ships.
    """
    if not isinstance(value, dict):
        return None
    field_type = value.get("type")
    if not isinstance(field_type, str):
        return None
    return BUILTIN_FIELD_TYPES.get(field_type)


def _rendered_field(shortcode, value):
    """Build the popup payload for a field, from whichever shortcode renders it.

    The shortcode renders the value into ``html``, which is what lets goodmap's own types and
    a plugin's alike display without shipping any frontend code. The entry's own keys travel
    alongside for a React field plugin rendering from the data instead - a bare value under
    the shortcode's ``content_key``, the name that plugin would look for. ``type`` is stamped
    last, so an entry cannot redirect its own field at another renderer.

    Because that bare value travels alongside, a shortcode's rendering is presentation, not
    concealment: one that masks or drops part of what it displays still ships the original
    here for anyone reading the response. Nothing in goodmap reads it - the popup needs only
    ``html`` and ``type`` - so it is carried purely for a field plugin that would rather
    render from the data, and could be dropped if none turns up wanting it.

    Args:
        shortcode: The Shortcode rendering this field.
        value: The field's value from the location data.

    Returns:
        The field payload, carrying at least ``type`` and ``html``.
    """
    entry = value if isinstance(value, dict) else {shortcode.content_key: value}
    return {**entry, "type": shortcode.name, "html": shortcode.render_value(value)}


def prepare_pin(place, visible_fields, meta_data, shortcodes=None) -> dict[str, Any]:
    """Format one location into the translated payload its map popup renders.

    Args:
        place: The location's data.
        visible_fields: Field names to show in the popup.
        meta_data: Field names to carry as metadata.
        shortcodes: Field name → the platzky Shortcode bound to it. A plugin claims a field
            by name; anything else may still name a built-in ``type`` in its own data (see
            :mod:`goodmap.field_types`). Either way one shortcode renders it.

    Returns:
        Title, subtitle, position, metadata, and ``data`` as ``[label, value]`` pairs.
    """
    plugins = shortcodes or {}
    data = []
    for field in visible_fields:
        if field not in place:
            continue
        value = safe_gettext(place[field])
        shortcode = plugins.get(field) or _builtin_shortcode(value)
        if shortcode is not None:
            value = _rendered_field(shortcode, value)
        elif isinstance(value, dict) and "html" in value:
            # ``html`` is this payload's word for "the server rendered this", and the popup
            # injects it as markup. Nothing rendered this field, so an ``html`` here came
            # from the data - a suggested point, an imported dataset - and must not be
            # mistaken for goodmap's own output.
            value = {key: item for key, item in value.items() if key != "html"}
        data.append([gettext(field), value])
    pin_data = {
        "title": place["name"],
        "subtitle": lazy_gettext(place["type_of_place"]),  # TODO this should not be obligatory
        "position": place["position"],
        "metadata": {
            gettext(field): safe_gettext(place[field]) for field in meta_data if field in place
        },
        "data": data,
    }
    return pin_data

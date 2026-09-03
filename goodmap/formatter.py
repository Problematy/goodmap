"""Formatters for translating and preparing location data for display."""

import logging
from typing import Any

from flask_babel import gettext, lazy_gettext

from goodmap.field_types import FIRST_PARTY_FIELD_TYPES

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


def _shortcode_field(shortcode, value):
    """Build the popup payload for a field a platzky shortcode is bound to.

    The shortcode renders the value into ``html``, which is what lets a plugin display a
    field without shipping any frontend code. The entry's own keys travel alongside for a
    React field plugin rendering from the data instead — a bare value under the shortcode's
    ``content_key``, the name that plugin would look for. ``type`` is stamped last, so an
    entry cannot redirect its own field at another renderer.

    Args:
        shortcode: The platzky Shortcode registered for this field name.
        value: The field's value from the location data.

    Returns:
        The field payload, carrying at least ``type`` and ``html``.
    """
    entry = value if isinstance(value, dict) else {shortcode.content_key: value}
    return {**entry, "type": shortcode.name, "html": shortcode.render_value(value)}


def _first_party_field(value):
    """Add ``html`` for a field whose stored ``type`` is one goodmap builds in.

    Reached only where no plugin shortcode claimed the field, and only the closed catalogue
    in :mod:`goodmap.field_types` is on offer — so an entry can never name its way to a
    plugin's renderer.

    Args:
        value: The field's value from the location data.

    Returns:
        The payload with ``html`` added, or ``value`` unchanged when its ``type`` is not
        one goodmap renders.
    """
    if not isinstance(value, dict):
        return value
    field_type = value.get("type")
    if not isinstance(field_type, str):
        return value
    render_html = FIRST_PARTY_FIELD_TYPES.get(field_type)
    if render_html is None:
        return value
    return {**value, "html": render_html(value)}


def prepare_pin(place, visible_fields, meta_data, shortcodes=None) -> dict[str, Any]:
    """Format one location into the translated payload its map popup renders.

    Args:
        place: The location's data.
        visible_fields: Field names to show in the popup.
        meta_data: Field names to carry as metadata.
        shortcodes: Field name → the platzky Shortcode bound to it. A match is rendered by
            :func:`_shortcode_field`, anything else by :func:`_first_party_field`.

    Returns:
        Title, subtitle, position, metadata, and ``data`` as ``[label, value]`` pairs.
    """
    plugins = shortcodes or {}
    data = []
    for field in visible_fields:
        if field not in place:
            continue
        value = safe_gettext(place[field])
        if field in plugins:
            value = _shortcode_field(plugins[field], value)
        else:
            value = _first_party_field(value)
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

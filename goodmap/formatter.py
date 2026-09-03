"""Formatters for translating and preparing location data for display."""

import logging

from flask_babel import gettext, lazy_gettext

logger = logging.getLogger(__name__)


def safe_gettext(text):
    """Safely apply gettext translation to various data types.

    Args:
        text: Text to translate (str, list, or dict)

    Returns:
        Translated text in same format as input
    """
    if isinstance(text, list):
        return list(map(gettext, text))
    elif isinstance(text, dict):
        return text
    else:
        return gettext(text)


def _shortcode_field(shortcode, value):
    """Build the marker-popup payload for a field backed by a platzky shortcode.

    The shortcode renders the value itself, so a plugin needs no frontend code here to
    be displayable — ``FieldRenderer`` seeds the field's fold with ``html`` when no
    first-party renderer claims the ``type``. The entry's own keys travel alongside for
    a React field plugin rendering from the data instead; a bare value is placed under
    the shortcode's ``content_key`` so such a plugin finds it under the name the
    shortcode uses. ``type`` is stamped last, so an entry cannot redirect its own field
    at another renderer.

    Args:
        shortcode: The platzky Shortcode registered for this field name.
        value: The field's value from the location data.

    Returns:
        dict: The field payload, carrying at least ``type`` and ``html``.
    """
    entry = value if isinstance(value, dict) else {shortcode.content_key: value}
    return {**entry, "type": shortcode.name, "html": shortcode.render_value(value)}


def prepare_pin(place, visible_fields, meta_data, shortcodes=None):
    """Prepare location data for map pin display with translations.

    Args:
        place: Location data dictionary
        visible_fields: List of field names to display in pin
        meta_data: List of metadata field names
        shortcodes: Optional mapping of field name → Shortcode instance.
            When a field name matches a shortcode, the value is replaced by this
            popup's field payload: the entry's own keys, the ``type`` the frontend
            routes on, and ``html`` — the shortcode's own rendering of the value.

    Returns:
        dict: Formatted pin data with title, subtitle, position, metadata, and translated fields
    """
    plugins = shortcodes or {}
    data = []
    for field in visible_fields:
        if field not in place:
            continue
        value = safe_gettext(place[field])
        if field in plugins:
            value = _shortcode_field(plugins[field], value)
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

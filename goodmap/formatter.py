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


def prepare_pin(place, visible_fields, meta_data, shortcodes=None):
    """Prepare location data for map pin display with translations.

    Args:
        place: Location data dictionary
        visible_fields: List of field names to display in pin
        meta_data: List of metadata field names
        shortcodes: Optional mapping of field name → Shortcode instance.
            When a field name matches a shortcode, its value is transformed via
            ``shortcode.transform_field_value()`` before display.

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
            value = plugins[field].transform_field_value(value)
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

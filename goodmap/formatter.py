"""Formatters for translating and preparing location data for display."""

from flask_babel import gettext, lazy_gettext


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


def prepare_pin(place, visible_fields, meta_data):
    """Prepare location data for map pin display with translations.

    Args:
        place: Location data dictionary
        visible_fields: List of field names to display in pin
        meta_data: List of metadata field names

    Returns:
        dict: Formatted pin data with title, subtitle, position, metadata, and translated fields
    """
    pin_data = {
        "title": place["name"],
        "subtitle": lazy_gettext(place["type_of_place"]),  # TODO this should not be obligatory
        "position": place["position"],
        "metadata": {
            gettext(field): safe_gettext(place[field]) for field in meta_data if field in place
        },
        "data": [
            [gettext(field), safe_gettext(place[field])]
            for field in visible_fields
            if field in place
        ],
    }
    return pin_data

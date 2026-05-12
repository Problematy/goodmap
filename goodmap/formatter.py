"""Formatters for translating and preparing location data for display."""

import base64
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


def _apply_field_plugin(value, field, field_plugins):
    """Wrap a dict field value with its plugin scope if a handler is registered.

    Returns:
        The wrapped dict with scope if registered, None if the value is an
        unconfigured plugin field, or the original value otherwise.
    """
    if isinstance(value, dict):
        if field in field_plugins:
            result = {"scope": field_plugins[field], **value}
            if isinstance(result.get("code"), str):
                result["code"] = base64.b64encode(result["code"].encode()).decode()
            return result
        if "code" in value and "type" not in value and "scope" not in value:
            logger.debug("Dropping field '%s': unconfigured plugin data %s", field, value)
            return None
    return value


def prepare_pin(place, visible_fields, meta_data, field_plugins=None):
    """Prepare location data for map pin display with translations.

    Args:
        place: Location data dictionary
        visible_fields: List of field names to display in pin
        meta_data: List of metadata field names
        field_plugins: Optional mapping of field name → plugin scope. Dict-valued
            fields listed here are wrapped with
            ``{"type": "plugin", "scope": ..., "props": ...}`` so the frontend
            can route them to the correct plugin component.

    Returns:
        dict: Formatted pin data with title, subtitle, position, metadata, and translated fields
    """
    plugins = field_plugins or {}
    data = []
    for field in visible_fields:
        if field not in place:
            continue
        processed = _apply_field_plugin(safe_gettext(place[field]), field, plugins)
        if processed is not None:
            data.append([gettext(field), processed])
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

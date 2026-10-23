"""Formatters for translating and preparing location data for display."""

from typing import Any

from flask_babel import gettext, lazy_gettext
from pydantic import JsonValue

from goodmap.field_types import BUILTIN_FIELD_TYPES


def safe_gettext(text):
    """Translate ``text``, mapping over a list; anything that is not text is left alone.

    A dict, a number or a position has nothing for ``gettext`` to look up, so it comes back
    as it is. Nor does an empty string: ``gettext("")`` is the catalogue's header.

    Args:
        text: A str, a list, or any other field value.

    Returns:
        The translation, in the same shape as the input.
    """
    if isinstance(text, str):
        return gettext(text) if text else text
    if isinstance(text, list):
        return [safe_gettext(item) for item in text]
    return text


def _find_builtin_shortcode(value):
    """The built-in shortcode a field's own data asks for, if any.

    Reached only where no plugin shortcode claimed the field by name, and only the closed
    catalogue in :mod:`goodmap.field_types` is on offer - so an entry can never name its way
    to a plugin's renderer.

    Args:
        value: The field's value from the location data.

    Returns:
        The Shortcode for the declared ``type``, or None when it names none goodmap ships.
    """
    field_type = value.get("type") if isinstance(value, dict) else None
    return BUILTIN_FIELD_TYPES.get(field_type) if isinstance(field_type, str) else None


def _render_field(shortcode, value):
    """Build the popup payload for a field, from whichever shortcode renders it.

    The shortcode renders the value into ``html``, which is what lets goodmap's own types and
    a plugin's alike display without shipping any frontend code. The entry's own keys travel
    alongside for a React field plugin rendering from the data instead - a bare value under
    the shortcode's ``content_key``. ``type`` is stamped last, so an entry cannot redirect
    its own field at another renderer.

    Args:
        shortcode: The Shortcode rendering this field.
        value: The field's value from the location data.

    Returns:
        The field payload, carrying at least ``type`` and ``html``.
    """
    entry = value if isinstance(value, dict) else {shortcode.content_key: value}
    return {**entry, "type": shortcode.name, "html": shortcode.render_value(value)}


def _drop_html_from_field(value: JsonValue) -> JsonValue:
    """Drop any ``html`` an unrendered field brought with it.

    ``html`` is this payload's word for "the server rendered this", and the popup injects it
    as markup. Nothing rendered this field, so an ``html`` here came from the data - a
    suggested point, an imported dataset - and must not be mistaken for goodmap's own output.

    Args:
        value: The field's value from the location data.

    Returns:
        The value without ``html``.
    """
    if not isinstance(value, dict):
        return value
    return {key: item for key, item in value.items() if key != "html"}


class PinFormatter:
    """Formats locations into the translated payload their map popups render.

    Built once at startup with every setting it needs, the fields to show included: like
    marker styles, they are read from the data source when the app starts, so changing them
    takes a restart.
    """

    def __init__(self, visible_fields, meta_fields, plugin_shortcodes=None):
        """Hold the formatting settings.

        Args:
            visible_fields: Field names to show in the popup, in order.
            meta_fields: Field names to carry as metadata.
            plugin_shortcodes: Field name -> the platzky Shortcode a plugin bound to it. A
                plugin claims a field by name; anything else may still name a built-in
                ``type`` in its own data (see :mod:`goodmap.field_types`). Either way one
                shortcode renders it.
        """
        self._visible_fields = visible_fields
        self._meta_fields = meta_fields
        self._plugin_shortcodes = plugin_shortcodes or {}

    def prepare_pin(self, place) -> dict[str, Any]:
        """Format one location.

        Args:
            place: The location's data.

        Returns:
            Title, subtitle, position, metadata, and ``data`` as ``[label, value]`` pairs.
        """
        return {
            "title": place["name"],
            "subtitle": lazy_gettext(place["type_of_place"]),  # TODO should not be obligatory
            "position": place["position"],
            # Machine data for the frontend (e.g. ``uuid`` for share links), read by its stored
            # key, so it is passed on untranslated.
            "metadata": {field: place[field] for field in self._meta_fields if field in place},
            "data": [
                entry
                for field in self._visible_fields
                if (entry := self._build_entry(place, field))
            ],
        }

    def _build_entry(self, place, field):
        """Build one field's ``[label, value]`` pair for the popup, both translated.

        Args:
            place: The location's data.
            field: The field's name.

        Returns:
            The pair, or None when the field has nothing to show: the place lacks it, its
            value is None (``model_dump`` keeps an unset optional field as None), or it
            rendered nothing.
        """
        if place.get(field) is None:
            return None
        value = safe_gettext(place[field])
        if field in self._plugin_shortcodes:
            value = _render_field(self._plugin_shortcodes[field], value)
        elif builtin := _find_builtin_shortcode(value):
            value = _render_field(builtin, value)
            if not value["html"]:
                # Goodmap's own types have nothing to show but their ``html``, so one that
                # rendered nothing - a refused image, say - would leave a label over a blank.
                return None
        else:
            value = _drop_html_from_field(value)
        return [gettext(field), value]

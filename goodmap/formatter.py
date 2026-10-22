"""Formatters for translating and preparing location data for display."""

import logging
from typing import Any

from flask_babel import gettext, lazy_gettext

from goodmap.field_types import BUILTIN_FIELD_TYPES, MULTI_VALUE_TYPES
from goodmap.translation import safe_gettext

logger = logging.getLogger(__name__)


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
    field_type = value.get("type") if isinstance(value, dict) else None
    return BUILTIN_FIELD_TYPES.get(field_type) if isinstance(field_type, str) else None


def _rendered_field(shortcode, value):
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


def _without_html(value):
    """Drop any ``html`` an unrendered field brought with it, its ``items`` included.

    ``html`` is this payload's word for "the server rendered this", and the popup injects it
    as markup. Nothing rendered this field, so an ``html`` here came from the data - a
    suggested point, an imported dataset - and must not be mistaken for goodmap's own output.

    Args:
        value: The field's value from the location data.

    Returns:
        The value without ``html``, at the top level or on any item.
    """
    if not isinstance(value, dict):
        return value
    stripped = {key: item for key, item in value.items() if key != "html"}
    if isinstance(stripped.get("items"), list):
        stripped["items"] = [_without_html(item) for item in stripped["items"]]
    return stripped


class PinFormatter:
    """Formats locations into the translated payload their map popups render.

    Built once at startup with every setting it needs, the fields to show included: like
    marker styles, they are read from the data source when the app starts, so changing them
    takes a restart.
    """

    def __init__(self, visible_fields, meta_fields, alt_template, shortcodes=None):
        """Hold the formatting settings.

        Args:
            visible_fields: Field names to show in the popup, in order.
            meta_fields: Field names to carry as metadata.
            alt_template: The compiled ``IMAGE_ALT_TEMPLATE`` (see :mod:`goodmap.alt_template`),
                describing the place to any image that does not describe itself. Its default
                lives in the config: the place's name.
            shortcodes: Field name -> the platzky Shortcode bound to it. A plugin claims a
                field by name; anything else may still name a built-in ``type`` in its own
                data (see :mod:`goodmap.field_types`). Either way one shortcode renders it.
        """
        self._visible_fields = visible_fields
        self._meta_fields = meta_fields
        self._alt_template = alt_template
        self._plugins = shortcodes or {}

    def prepare_pin(self, place) -> dict[str, Any]:
        """Format one location.

        Args:
            place: The location's data.

        Returns:
            Title, subtitle, position, metadata, and ``data`` as ``[label, value]`` pairs.
        """
        entries = (self._entry(place, field) for field in self._visible_fields if field in place)
        return {
            "title": place["name"],
            "subtitle": lazy_gettext(place["type_of_place"]),  # TODO should not be obligatory
            "position": place["position"],
            "metadata": {
                gettext(field): safe_gettext(place[field])
                for field in self._meta_fields
                if field in place
            },
            "data": [entry for entry in entries if entry is not None],
        }

    def _entry(self, place, field):
        """Build one field's ``[label, value]`` pair for the popup, both translated.

        Args:
            place: The location's data.
            field: The field's name.

        Returns:
            The pair, or None when the field has nothing to show.
        """
        value = safe_gettext(place[field])
        if field in self._plugins:
            value = _rendered_field(self._plugins[field], value)
        elif builtin := _builtin_shortcode(value):
            value = self._rendered_builtin(place, builtin, value)
            if not value["html"]:
                # Goodmap's own types have nothing to show but their ``html``, so one that
                # rendered nothing - every image refused - would leave a label over a blank.
                return None
        else:
            value = _without_html(value)
        return [gettext(field), value]

    def _rendered_builtin(self, place, shortcode, value):
        """Build the payload for a field naming one of goodmap's own types.

        Two things only goodmap's own types get, because goodmap knows what their rendering
        means - a plugin's field keeps exactly the rendering its shortcode gives it:

        * ``items``: a field of a :data:`~goodmap.field_types.MULTI_VALUE_TYPES` type - an
          image field - holding several values lists them there. Each is rendered on its own
          and the renderings joined into the field's ``html``; the items themselves go back
          as data, without ``html``. An item the shortcode refuses renders to nothing and is
          dropped, as is one that is not an object. Any other type with ``items`` renders
          nothing, with a warning. A gallery wanting its own layout binds its own shortcode
          to the field, or the field names the gallery's type instead.
        * an ``alt`` from :attr:`_alt_template`, for a type that declares one. An entry's own
          value wins; a ``null`` counts as absent, so imported data with ``"alt": null`` is
          still described rather than marked decorative.

        Args:
            place: The location's data, which the alt template describes.
            shortcode: The built-in Shortcode the field's ``type`` named.
            value: The field's value from the location data - a dict, since it named a type.

        Returns:
            The field payload, carrying ``type`` and ``html``, and ``items`` when it had them.
        """
        declared = {attribute.name for attribute in shortcode.attributes}
        fallback = {"alt": self._alt_template.render(place)} if "alt" in declared else {}

        def rendered(entry):
            given = {key: item for key, item in entry.items() if item is not None}
            return _rendered_field(shortcode, {**fallback, **given})

        if not isinstance(value.get("items"), list):
            return rendered(value)
        if shortcode.name not in MULTI_VALUE_TYPES:
            logger.warning("A %s field holds one value; items is for images.", shortcode.name)
            return {**value, "type": shortcode.name, "html": ""}
        if not all(isinstance(item, dict) for item in value["items"]):
            logger.warning("Dropping %s items that are not objects.", shortcode.name)
        items = [rendered(item) for item in value["items"] if isinstance(item, dict)]
        items = [item for item in items if item["html"]]
        html = "".join(item["html"] for item in items)
        data = [{k: v for k, v in item.items() if k not in ("type", "html")} for item in items]
        return {**value, "items": data, "type": shortcode.name, "html": html}

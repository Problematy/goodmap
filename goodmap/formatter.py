"""Formatters for translating and preparing location data for display."""

import logging
from typing import Any

from flask_babel import gettext, lazy_gettext

from goodmap.alt_template import DEFAULT_ALT_TEMPLATE, AltTemplate
from goodmap.field_types import BUILTIN_FIELD_TYPES, ITEM_SEPARATORS

logger = logging.getLogger(__name__)

#: What a caller that passes no ``IMAGE_ALT_TEMPLATE`` gets: the place's name, as configured.
_DEFAULT_ALT_TEMPLATE = AltTemplate(DEFAULT_ALT_TEMPLATE)


def safe_gettext(text):
    """Translate ``text``, mapping over a list; anything that is not text is left alone.

    A dict, a number or a position has nothing for ``gettext`` to look up, so it comes back
    as it is - which is what lets one helper translate popup values and alt template
    context alike. Nor does an empty string: ``gettext("")`` is the catalogue's header.

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


def _rendered_builtin(shortcode, value, defaults):
    """Build the payload for a field naming one of goodmap's own types.

    Two things only goodmap's own types get, because goodmap knows what their rendering
    means - a plugin's field keeps exactly the rendering its shortcode gives it:

    * ``items``: a field holding several values lists them there. Each is rendered on its
      own and the renderings joined into the field's ``html``, with the type's
      :data:`~goodmap.field_types.ITEM_SEPARATORS` entry between; the items themselves go
      back as data, without ``html``. An item the shortcode refuses renders to nothing and
      is dropped, as is one that is not an object. A gallery wanting its own layout binds
      its own shortcode to the field, or the field names the gallery's type instead.
    * defaults derived from the place, such as an image's ``alt``. An entry's own value wins;
      a ``null`` counts as absent, so imported data with ``"alt": null`` is still described
      rather than marked decorative.

    Args:
        shortcode: The built-in Shortcode the field's ``type`` named.
        value: The field's value from the location data - a dict, since it named a type.
        defaults: ``defaults(shortcode)`` -> the place-derived attributes it declares.

    Returns:
        The field payload, carrying ``type`` and ``html``, and ``items`` when it had them.
    """
    fallback = defaults(shortcode)

    def rendered(entry):
        given = {key: item for key, item in entry.items() if item is not None}
        return _rendered_field(shortcode, {**fallback, **given})

    if not isinstance(value.get("items"), list):
        return rendered(value)
    entries = value["items"]
    if not all(isinstance(item, dict) for item in entries):
        logger.warning(
            "Dropping %s items that are not objects; write each as e.g. {%r: ...}.",
            shortcode.name,
            next(iter(shortcode.attributes)).name,
        )
    items = [rendered(item) for item in entries if isinstance(item, dict)]
    items = [item for item in items if item["html"]]
    html = ITEM_SEPARATORS.get(shortcode.name, "").join(item["html"] for item in items)
    data = [{k: v for k, v in item.items() if k not in ("type", "html")} for item in items]
    return {**value, "items": data, "type": shortcode.name, "html": html}


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


def _popup_entry(field, value, plugins, defaults):
    """Build one field's ``[label, value]`` pair for the popup, both translated.

    Args:
        field: The field's name.
        value: Its value from the location data.
        plugins: Field name -> the plugin Shortcode bound to it.
        defaults: ``defaults(shortcode)`` -> the place-derived attributes it declares.

    Returns:
        The pair, or None when the field has nothing to show.
    """
    value = safe_gettext(value)
    if field in plugins:
        value = _rendered_field(plugins[field], value)
    elif builtin := _builtin_shortcode(value):
        value = _rendered_builtin(builtin, value, defaults)
        if not value["html"]:
            # Goodmap's own types have nothing to show but their ``html``, so one that
            # rendered nothing - every image refused - would leave a label over a blank.
            return None
    else:
        value = _without_html(value)
    return [gettext(field), value]


def prepare_pin(
    place, visible_fields, meta_data, shortcodes=None, alt_template=None
) -> dict[str, Any]:
    """Format one location into the translated payload its map popup renders.

    Args:
        place: The location's data.
        visible_fields: Field names to show in the popup.
        meta_data: Field names to carry as metadata.
        shortcodes: Field name → the platzky Shortcode bound to it. A plugin claims a field
            by name; anything else may still name a built-in ``type`` in its own data (see
            :mod:`goodmap.field_types`). Either way one shortcode renders it.
        alt_template: The compiled ``IMAGE_ALT_TEMPLATE`` (see :mod:`goodmap.alt_template`),
            describing the place to any image that does not describe itself. Omitted, the
            place's name does, as when the key is not configured.

    Returns:
        Title, subtitle, position, metadata, and ``data`` as ``[label, value]`` pairs.
    """
    plugins = shortcodes or {}
    alt = None

    def defaults(shortcode):
        # Rendered once per pin, and only once an image asks for it.
        nonlocal alt
        if "alt" not in {attribute.name for attribute in shortcode.attributes}:
            return {}
        if alt is None:
            alt = (alt_template or _DEFAULT_ALT_TEMPLATE).render(place, safe_gettext)
        return {"alt": alt}

    entries = (
        _popup_entry(field, place[field], plugins, defaults)
        for field in visible_fields
        if field in place
    )
    pin_data = {
        "title": place["name"],
        "subtitle": lazy_gettext(place["type_of_place"]),  # TODO this should not be obligatory
        "position": place["position"],
        "metadata": {
            gettext(field): safe_gettext(place[field]) for field in meta_data if field in place
        },
        "data": [entry for entry in entries if entry is not None],
    }
    return pin_data

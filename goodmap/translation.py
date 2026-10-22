"""Translating location field values into the request's language."""

from flask_babel import gettext


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

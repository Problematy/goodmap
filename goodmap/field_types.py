"""Marker-field types goodmap renders itself, rather than leaving to a plugin.

A field's value may name a ``type`` in the data — ``{"type": "hyperlink", "value": …}`` —
and the types named here are the ones goodmap answers for. They are rendered on the server
into the ``html`` the popup displays, the same way a plugin's shortcode field is, so the
frontend needs no component per type and there is no second copy of the rules below living
in JavaScript.

The set is closed and first-party, which is what makes it safe to resolve a renderer from
the data at all: a location entry can ask for a type in here and nothing else, so it can
never point itself at a plugin's renderer. ``prepare_pin`` consults it only for a field no
plugin shortcode is bound to, so a plugin still owns its own field outright.
"""

from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from markupsafe import escape
from platzky.shortcodes import LINK_URL_POLICY, UrlNotPermitted
from platzky.shortcodes.link import link_shortcode

#: Schemes that navigate the browser somewhere, and so are worth a new tab.
_NEW_TAB_SCHEMES = frozenset({"http", "https"})


def _link_html(entry: dict[str, Any]) -> str:
    """Render a link field: ``value`` is where it goes, ``displayValue`` what it reads.

    The URL policy is platzky's, not a second one written here — the whole point of
    rendering this server-side is that ``[link]`` in a post and a ``hyperlink`` field on a
    marker agree about what may be linked to, including ``mailto:`` and ``tel:``, which a
    place's contact details are routinely written as.

    A URL that policy refuses still renders its text, escaped and unlinked. Dropping the
    field entirely would leave its label sitting above a blank, and the text is usually the
    part a reader wanted; it is also what keeps a wrapper plugin attached to ``hyperlink``
    from receiving nothing to wrap.

    Args:
        entry: The field value as stored, carrying ``value`` and optionally ``displayValue``.

    Returns:
        An anchor, or just the escaped link text when the URL is not one we may emit.
    """
    url = str(entry.get("value") or "")
    text = str(entry.get("displayValue") or url)
    try:
        LINK_URL_POLICY.check(url)
    except UrlNotPermitted:
        # Asked before rendering rather than caught after: ``render_value`` answers a refusal
        # by dropping the element, and a field wants its text kept instead.
        return str(escape(text))
    # A new tab is for leaving the site; handing a mailto: or tel: to the mail client or
    # dialer navigates nowhere, and asking for one anyway leaves a blank tab behind.
    external = urlparse(url).scheme in _NEW_TAB_SCHEMES
    attrs = {"url": url, "content": text} | ({"target": "_blank"} if external else {})
    return link_shortcode.render_value(attrs)


#: Field ``type`` → the renderer producing its HTML. Keyed by the name written in the data.
#:
#: ``hyperlink`` and ``CTA`` share a renderer because they only ever differed in presentation:
#: both are a URL and the text to show for it. Which one a field is decides where the popup
#: puts it and how it is styled — a line among the details, or a button below them — and that
#: is ``LocationDetails``' business, decided from the field name it already groups on. The
#: ``type`` travels on the payload either way, so a field plugin can still attach to just one.
FIRST_PARTY_FIELD_TYPES: dict[str, Callable[[dict[str, Any]], str]] = {
    "hyperlink": _link_html,
    "CTA": _link_html,
}

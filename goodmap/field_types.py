"""Goodmap's built-in marker field types.

A location entry names a field's ``type`` in the data — ``{"type": "hyperlink", "value": …}``
— and this module is the catalogue of the types goodmap ships. Each renders on the server
into the ``html`` the popup shows, so none needs a React component or a second copy of the
rules below in JavaScript.

The catalogue is closed, which is what makes it safe to pick a renderer from the data at
all: an entry may name a type in here and nothing else.
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

    The URL policy is platzky's rather than a second one written here, so ``[link]`` in a
    post and a ``hyperlink`` on a marker agree on what may be linked to — ``mailto:`` and
    ``tel:`` included, which is how a place's contact details are routinely written.

    A refused URL still renders its text, escaped and unlinked: the label would otherwise
    sit above a blank, and a wrapper plugin on ``hyperlink`` would get nothing to wrap.
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

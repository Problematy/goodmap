"""Goodmap's built-in marker field types.

A location entry names a field's ``type`` in the data - ``{"type": "hyperlink", "value": …}``
- and this module is the catalogue of the types goodmap ships. Each is an ordinary platzky
``Shortcode``, the same thing a plugin contributes, so every field renders through one
interface and the popup gets ``html`` either way.

What differs is how a renderer is found. A plugin's shortcode is bound to a field by *name*,
which is what makes the field its own. Goodmap's own are looked up by the ``type`` the entry
declares, so any field can ask to be a ``hyperlink`` whatever it is called. That lookup is
safe only because this catalogue is closed: an entry may name a type in here and nothing
else, and so can never point itself at a plugin's renderer.

The catalogue is goodmap's own types plus one of platzky's built-ins - ``image``, so a
place can carry photos; platzky holds its URLs to ``https`` or a path on the site. One
rather than the whole set, because the entries naming these types are data nobody vouched
for, and platzky's ``html`` would hand them raw markup in the popup.

An image field holds one image - ``{"type": "image", "url": …, "alt": …}`` - described by
the ``alt`` its data gives it.
"""

from collections.abc import Sequence
from urllib.parse import urlparse

from markupsafe import Markup, escape
from platzky.shortcodes import Shortcode, ShortcodeAttr, ShortcodeAttrs, UrlNotPermitted
from platzky.shortcodes.image import image_shortcode
from platzky.shortcodes.link import LinkShortcode

#: Schemes that navigate the browser somewhere, and so are worth a new tab.
_NEW_TAB_SCHEMES = frozenset({"http", "https"})


class HyperlinkFieldShortcode(LinkShortcode):
    """A marker field holding a URL, rendered as a link.

    Subclasses platzky's ``[link]`` rather than restating it, so a link in a post and a link
    on a marker agree on what may be linked to - ``mailto:`` and ``tel:`` included, which is
    how a place's contact details are routinely written - and produce the same anchor.

    The field's own shape is declared rather than adapted to: ``value`` is where the link
    goes, ``displayValue`` what it reads, and ``content_key`` makes the latter the inner
    content so an absent one falls back to the URL, which ``render_value`` already does.
    """

    name = "hyperlink"
    description = "A marker field holding a URL, shown as a link."
    content_key = "displayValue"
    attributes = ShortcodeAttrs(
        [
            ShortcodeAttr("value", "Where the link goes", required=True),
            ShortcodeAttr("displayValue", "Text to show for it", required=False),
        ]
    )

    def render(self, attrs: ShortcodeAttrs, content: str, children: Sequence[Markup]) -> str:
        """Render the anchor, keeping the text when the URL is refused.

        A refusal reaches ``render_value`` as a dropped element, which suits a link written
        in prose but not a field: the label would be left sitting above a blank, the text is
        usually the part a reader wanted, and a wrapper plugin attached to this type would
        receive nothing to wrap. So it is caught here and the text kept, escaped and
        unlinked.

        Args:
            attrs: The field's stored keys, ``value`` among them.
            content: The link text, already escaped.
            children: Element children, passed through to ``[link]``.

        Returns:
            An anchor, or just the link text when the URL is not one we may emit.
        """
        url = str(attrs.value or "")
        # ``render_value`` falls back to ``value`` only when ``displayValue`` is absent; a
        # present-but-empty one would otherwise render an anchor with nothing to click.
        content = content or escape(url)
        link_attrs = ShortcodeAttrs(list(LinkShortcode.attributes))
        link_attrs.values = {"url": url}
        # A new tab is for leaving the site; handing a mailto: or tel: to the mail client or
        # dialer navigates nowhere, and asking for one anyway leaves a blank tab behind.
        if urlparse(url).scheme in _NEW_TAB_SCHEMES:
            link_attrs.values["target"] = "_blank"
        try:
            return super().render(link_attrs, content, children)
        except UrlNotPermitted:
            return str(content)


class CTAFieldShortcode(HyperlinkFieldShortcode):
    """The same link, shown as a button below the details rather than among them.

    ``hyperlink`` and ``CTA`` only ever differed in presentation - both are a URL and the
    text to show for it - and where the popup puts one is ``LocationDetails``' business,
    decided from the field name it already groups on. The ``type`` travels on the payload
    either way, so a field plugin can still attach to just one of them.
    """

    name = "CTA"
    description = "A marker field holding a URL, shown as a call-to-action button."


#: Field ``type`` -> the shortcode rendering it, keyed by the name written in the data. Of
#: platzky's built-ins only ``image`` is here: ``html`` would let an entry nobody vouched
#: for emit raw markup into the popup.
BUILTIN_FIELD_TYPES: dict[str, Shortcode] = {
    s.name: s for s in (image_shortcode, HyperlinkFieldShortcode(), CTAFieldShortcode())
}

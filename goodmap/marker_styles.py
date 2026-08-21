"""Resolves configured marker_styles.icons entries into plain, browser-ready URLs.

Runs once at app startup (see goodmap.create_app_from_config), turning the tagged
``{"provider": ..., "value": ...}`` form a data source may use into flat
``{icon_field_value: url}`` entries. window.MARKER_STYLES.icons is therefore always a
plain lookup table, so supporting a new provider needs no frontend release - the
separately versioned frontend bundle only ever has to understand URL strings.
"""

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class IconProvider(Protocol):
    """Turns one configured icon ``value`` into a browser-ready URL.

    A protocol rather than a base class: a provider is only ever looked up by name in
    ICON_PROVIDERS, so there is nothing to gain from making implementers inherit from us.
    """

    def resolve(self, value: str) -> str:
        """Build the URL this provider serves for ``value``."""
        ...


class PhosphorIconProvider:
    """Phosphor Icons (MIT), served from jsdelivr.

    ``value`` is an icon name in kebab-case, matching a filename in
    ``@phosphor-icons/core/assets/<weight>`` without its ``-<weight>.svg`` suffix, e.g.
    "shipping-container". Not validated against the actual icon set - an unknown name
    just 404s in the browser, the same as any other mistyped URL.
    """

    CDN_BASE = "https://cdn.jsdelivr.net/npm/@phosphor-icons/core@2/assets"
    WEIGHT = "fill"

    def resolve(self, value: str) -> str:
        """Build the CDN URL for the Phosphor icon named ``value``."""
        return f"{self.CDN_BASE}/{self.WEIGHT}/{value}-{self.WEIGHT}.svg"


class DirectUrlProvider:
    """A URL the deployment hosts itself, used exactly as configured."""

    def resolve(self, value: str) -> str:
        """Return ``value`` unchanged - it is already a URL."""
        return value


# Every icon provider a data source may name. Adding one is a class plus an entry here;
# nothing downstream - and no frontend release - has to know about it, because what
# reaches the browser is always a finished URL.
ICON_PROVIDERS: dict[str, IconProvider] = {
    "phosphor": PhosphorIconProvider(),
    "url": DirectUrlProvider(),
}


def _resolve_icon_entry(key: Any, entry: Any) -> str | None:
    """Resolve one marker_styles.icons entry to a usable URL.

    Args:
        key: The icons key this entry sits under, used only to name it in the warning
            logged when the entry cannot be resolved.
        entry: The raw entry - a plain URL string, a tagged
            {"provider": <name in ICON_PROVIDERS>, "value": str} dict, or malformed data.

    Returns:
        The resolved URL, or None if the entry is unresolvable (already logged).
    """
    if isinstance(entry, str):
        # A bare string is shorthand for the "url" provider, so both spellings resolve
        # by the same path rather than one of them short-circuiting.
        name, value = "url", entry
    elif isinstance(entry, dict):
        name, value = entry.get("provider"), entry.get("value")
    else:
        logger.warning(
            "marker_styles.icons['%s'] is neither a URL string nor a {provider, value} "
            "object; ignoring it",
            key,
        )
        return None

    if not isinstance(value, str) or not value:
        logger.warning("marker_styles.icons['%s'] has no usable 'value'; ignoring it", key)
        return None

    # The isinstance check comes first because an unhashable provider - a list, say -
    # would make .get() raise TypeError rather than miss.
    provider = ICON_PROVIDERS.get(name) if isinstance(name, str) else None
    if provider is None:
        logger.warning("marker_styles.icons['%s'] has unknown provider %r; ignoring it", key, name)
        return None

    return provider.resolve(value)


def resolve_marker_styles(marker_styles: dict[str, Any]) -> dict[str, Any]:
    """Resolve marker_styles.icons into a flat {value: url} lookup table.

    An entry that cannot be resolved is dropped with a warning naming it, rather than
    aborting startup: a typo in one icon costs that pin its icon, not the whole map.

    Args:
        marker_styles: Raw marker_styles config as returned by
            goodmap.db.get_marker_styles(). May be empty or lack an "icons" key. Never
            mutated - for the json backend this is the db's live in-memory config, so
            resolving in place would rewrite what the deployment has stored.

    Returns:
        A new dict. "icons", if present, is replaced by a flat {value: url} map with
        unresolvable entries omitted; every other key (icon_field, color_field, colors)
        is carried through untouched. "colors" needs no resolving - it maps straight to
        CSS colors and never had a tagged form.
    """
    icons = marker_styles.get("icons")

    if icons is None:
        return dict(marker_styles)

    if not isinstance(icons, dict):
        logger.warning("marker_styles.icons is not an object; ignoring it entirely")
        return {**marker_styles, "icons": {}}

    return {
        **marker_styles,
        "icons": {
            key: url
            for key, entry in icons.items()
            if (url := _resolve_icon_entry(key, entry)) is not None
        },
    }

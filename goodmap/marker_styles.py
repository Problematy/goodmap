"""Resolves configured marker_styles.icons entries into plain, browser-ready URLs.

Runs once at app startup (see goodmap.create_app_from_config), turning the tagged
``{"provider": ..., "value": ...}`` form a data source may use into flat
``{icon_field_value: url}`` entries. window.MARKER_STYLES.icons is therefore always a
plain lookup table, so supporting a new provider needs no frontend release - the
separately versioned frontend bundle only ever has to understand URL strings.
"""

from typing import Any, Protocol


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


def _icon_url(entry: Any) -> str:
    """The URL one marker_styles.icons entry stands for.

    Args:
        entry: A plain URL string - shorthand for the "url" provider - or a tagged
            {"provider": <name in ICON_PROVIDERS>, "value": str} dict.

    Returns:
        The resolved URL.

    Raises:
        KeyError, TypeError: The entry is malformed. Deliberately not caught: bad
            marker_styles config stops the app from starting, the same way a category
            with no allowed values does (see data_models.location.create_location_model).
    """
    if isinstance(entry, str):
        return ICON_PROVIDERS["url"].resolve(entry)
    return ICON_PROVIDERS[entry["provider"]].resolve(entry["value"])


def resolve_marker_styles(marker_styles: dict[str, Any]) -> dict[str, Any]:
    """Resolve marker_styles.icons into a flat {value: url} lookup table.

    Args:
        marker_styles: Raw marker_styles config as returned by
            goodmap.db.get_marker_styles(). May be empty or lack an "icons" key. Never
            mutated - for the json backend this is the db's live in-memory config, so
            resolving in place would rewrite what the deployment has stored.

    Returns:
        A new dict. "icons", if present, is replaced by a flat {value: url} map; every
        other key (icon_field, color_field, colors) is carried through untouched.
        "colors" needs no resolving - it maps straight to CSS colors and never had a
        tagged form.

    Raises:
        AttributeError, KeyError, TypeError: marker_styles.icons is malformed; see
            _icon_url. Uncaught by design, so the app refuses to start.
    """
    icons = marker_styles.get("icons")
    if icons is None:
        return dict(marker_styles)

    return {**marker_styles, "icons": {key: _icon_url(entry) for key, entry in icons.items()}}

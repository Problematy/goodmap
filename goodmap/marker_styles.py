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


def resolve_marker_styles(marker_styles: dict[str, Any]) -> dict[str, Any]:
    """Resolve marker_styles.icons into a flat {value: url} lookup table.

    One "icon_provider" serves the whole table, so every entry is a plain value that
    provider understands - a Phosphor icon name, a URL - rather than each one restating
    which provider it came from.

    Args:
        marker_styles: Raw marker_styles config as returned by
            goodmap.db.get_marker_styles(). Carries "icon_provider" (a name in
            ICON_PROVIDERS) whenever it carries "icons". May be empty or lack both.
            Never mutated - for the json backend this is the db's live in-memory config,
            so resolving in place would rewrite what is stored.

    Returns:
        A new dict. "icons", if present, is replaced by a flat {value: url} map; every
        other key (icon_field, color_field, colors) is carried through untouched.
        "colors" needs no resolving - it maps straight to CSS colors, with no provider.

    Raises:
        KeyError, TypeError: "icon_provider" is missing or names a provider that does
            not exist. Uncaught by design: bad config stops the app from starting, the
            same way a category with no allowed values does (see
            data_models.location.create_location_model).
    """
    resolved = dict(marker_styles)
    if icons := marker_styles.get("icons"):
        provider = ICON_PROVIDERS[marker_styles["icon_provider"]]
        resolved["icons"] = {key: provider.resolve(value) for key, value in icons.items()}
    return resolved

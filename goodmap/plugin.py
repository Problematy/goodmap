"""Base class for goodmap map plugins."""

from typing import Any

from platzky.plugin.plugin import PluginBase


class GoodmapPluginBase(PluginBase):
    """Base class (family root) for goodmap plugin capabilities.

    A goodmap plugin declares its frontend capabilities by subclassing the concrete
    capability bases below (one or more). goodmap derives each capability's manifest
    token and Module Federation module from the base class name — ``MapOverlayPluginBase``
    -> capability ``"MapOverlay"`` exposed as ``"./MapOverlay"`` — so the class is the
    single source of truth and there is no separate identifier to keep in sync.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)


class MapOverlayPluginBase(GoodmapPluginBase):
    """Capability: a plugin that renders an overlay on top of the map view.

    Map-overlay plugins contribute a frontend component (served via Module
    Federation) that is mounted globally over the map — e.g. a banner shown when
    no points are visible. They do not transform point/location data; for that,
    use platzky's ``ContentTransformerPluginBase`` instead.

    goodmap registers this capability with platzky (via ``extra_plugin_bases``)
    so overlay plugins are config-gated through the standard plugin loader.

    Manifest capability ``"MapOverlay"``; component exposed as ``"./MapOverlay"``.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)


class MarkerFieldPluginBase(GoodmapPluginBase):
    """Capability: a plugin that renders (or wraps) a marker-popup field.

    Every field plugin is the same kind of thing — a *wrapper* in the field's rendering
    fold, mounted by ``FieldRenderer``. Its ``config`` declares:

    - ``field``: the field ``type`` it attaches to (e.g. ``"hyperlink"``, or a custom type
      whose value the plugin's platzky shortcode produces as ``{"type": "<field>", ...}``).
    - ``order`` (optional): its position in the stack — lower is more innermost; ties keep
      registration order.

    ``FieldRenderer`` seeds the rendering with the built-in for the type (or a string) and
    folds every plugin for that ``field`` around it, innermost-first. Each plugin's component
    receives ``{ value, children, config }``: a "renderer" ignores ``children`` and renders
    from ``value``; a "decorator" composes around ``children``. (There is no separate
    renderer vs decorator role — the innermost is simply the one whose ``children`` is the
    seed.)

    goodmap registers this capability with platzky (via ``extra_plugin_bases``) so field
    plugins are config-gated through the standard plugin loader.

    Manifest capability ``"MarkerField"``; component exposed as ``"./MarkerField"``.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)


# The frontend plugin capabilities goodmap defines: registered with platzky (so plugins
# subclassing them are recognised and config-gated) and used to derive each plugin's
# manifest entries. A plugin may subclass one or more of these.
CAPABILITY_BASES: tuple[type[GoodmapPluginBase], ...] = (
    MapOverlayPluginBase,
    MarkerFieldPluginBase,
)

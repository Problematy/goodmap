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
    """Capability: a plugin that renders a single location field inside a marker popup.

    Field plugins contribute a frontend component (served via Module Federation) that
    renders a marker field whose ``type`` matches the plugin. The field's value is
    produced by the plugin's platzky shortcode as ``{"type": "<name>", ...}`` and mounted
    by ``FieldRenderer`` on the frontend, which resolves ``type`` to the component.

    goodmap registers this capability with platzky (via ``extra_plugin_bases``) so field
    plugins are config-gated through the standard plugin loader.

    Manifest capability ``"MarkerField"``; component exposed as ``"./MarkerField"``.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)


class MarkerFieldDecoratorPluginBase(GoodmapPluginBase):
    """Capability: a plugin that decorates (wraps) another field renderer's output.

    A decorator's frontend component receives the base renderer's already-rendered
    output as ``children`` and composes around it (icon, badge, tracking wrapper,
    styling). The base renderer still runs, so first-party behaviour — e.g. the URL
    sanitization in the built-in link/button — cannot be bypassed. The field ``type``
    a decorator wraps is taken from its ``config`` (``{"decorates": "<type>"}``).

    goodmap registers this capability with platzky (via ``extra_plugin_bases``) so
    decorator plugins are config-gated through the standard plugin loader.

    Manifest capability ``"MarkerFieldDecorator"``; component exposed as
    ``"./MarkerFieldDecorator"``.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)


# The frontend plugin capabilities goodmap defines: registered with platzky (so plugins
# subclassing them are recognised and config-gated) and used to derive each plugin's
# manifest entries. A plugin may subclass one or more of these.
CAPABILITY_BASES: tuple[type[GoodmapPluginBase], ...] = (
    MapOverlayPluginBase,
    MarkerFieldPluginBase,
    MarkerFieldDecoratorPluginBase,
)

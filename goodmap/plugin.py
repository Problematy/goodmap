"""Base class for goodmap map plugins."""

from typing import Any, ClassVar

from platzky.plugin.plugin import PluginBase


class GoodmapPluginBase(PluginBase):
    """Base class (family root) for goodmap plugin capabilities.

    Each concrete subclass declares a ``capability`` — a stable identifier for the
    integration point the plugin provides (recorded in ``PLUGIN_MANIFEST`` and used
    by the frontend to route the plugin to its handler) — and the ``module``, the
    Module Federation key under which the frontend component for that capability is
    exposed. A plugin may subclass **several** capability bases; goodmap emits one
    manifest entry per capability, each pointing at that capability's ``module``, all
    served from the plugin's single ``remoteEntry.js``.
    """

    capability: ClassVar[str]
    module: ClassVar[str]

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
    """

    capability: ClassVar[str] = "overlay"
    module: ClassVar[str] = "./MapOverlay"

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
    """

    capability: ClassVar[str] = "field"
    module: ClassVar[str] = "./MarkerField"

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
    """

    capability: ClassVar[str] = "field-decorator"
    module: ClassVar[str] = "./MarkerFieldDecorator"

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

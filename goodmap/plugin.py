"""Base class for goodmap map plugins."""

from typing import Any, ClassVar

from platzky.plugin.plugin import PluginBase


class GoodmapPluginBase(PluginBase):
    """Base class (family root) for goodmap plugin capabilities.

    Each concrete subclass declares ``capability`` — a stable identifier for the
    integration point the plugin provides (recorded in ``PLUGIN_MANIFEST`` and
    used by the frontend to route the plugin to its handler). Some capabilities
    mount a component at a location (e.g. ``overlay`` over the map, ``field`` in
    a marker); others alter behaviour with no fixed placement (e.g. swapping the
    tile engine). ``capability`` names *what the plugin is*, independent of where
    — or whether — it renders.
    """

    capability: ClassVar[str]

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

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

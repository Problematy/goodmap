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

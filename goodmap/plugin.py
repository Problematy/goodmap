"""Base class for goodmap map plugins."""

from typing import Any

from platzky.plugin.plugin import PluginBase


class GoodmapPluginBase(PluginBase):
    """Base class for goodmap map plugins."""

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

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

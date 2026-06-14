"""Base class for goodmap map plugins."""

from typing import Any

from platzky.plugin.plugin import PluginBase


class GoodmapPluginBase(PluginBase):
    """Base class for goodmap map plugins."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

"""Goodmap-aware plugin base class."""

from typing import ClassVar

from platzky.engine import Engine
from platzky.plugin.plugin import PluginBase


class GoodmapPlugin(PluginBase):
    """Plugin base for goodmap-aware plugins.

    Subclasses declare which location data fields they render by setting the
    ``field_renderers`` class attribute. Goodmap collects these from
    ``app.loaded_plugins`` after plugin loading completes.
    """

    field_renderers: ClassVar[dict[str, str]] = {}

    def process(self, app: Engine) -> Engine:
        """Base implementation — subclasses override and call super()."""
        return app

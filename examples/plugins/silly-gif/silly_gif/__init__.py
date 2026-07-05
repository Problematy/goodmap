"""Example goodmap plugin declaring two frontend capabilities.

``SillyGifPlugin`` subclasses two goodmap capability bases, so goodmap manifests it once
per capability (see ``PLUGIN_MANIFEST``), both served from the plugin's single
``remoteEntry.js``:

- :class:`~goodmap.plugin.MapOverlayPluginBase` -> capability ``"MapOverlay"``, component
  ``./MapOverlay``: a gif shown over the map while it loads.
- :class:`~goodmap.plugin.MarkerFieldPluginBase` -> capability ``"MarkerField"``, component
  ``./MarkerField``: a gif rendered for marker fields valued
  ``{"type": "silly_gif", "gif": "<url>"}``.

That's the whole backend: a plugin is *what capabilities it subclasses*. The two React
components live under ``frontend/src`` and are wired up by ``frontend/webpack.config.js``.
"""

from typing import Any

from goodmap.plugin import MapOverlayPluginBase, MarkerFieldPluginBase


class SillyGifPlugin(MapOverlayPluginBase, MarkerFieldPluginBase):
    """A silly gif, both as a map-loading overlay and inside marker fields."""

    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)

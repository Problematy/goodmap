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
    """Capability: a plugin that renders a marker-popup field — as the base renderer or as
    a decorator that wraps one.

    A field plugin's component is mounted by ``FieldRenderer`` and plays one of two roles,
    chosen by its ``config``:

    - **Renderer** (no ``config.decorates``): it *is* the component for the field ``type``
      matching its name. It receives the field value spread as props and renders it — the
      base of the field's rendering. The value comes from the plugin's platzky shortcode as
      ``{"type": "<name>", ...}``.
    - **Decorator** (``config.decorates`` set to a field ``type``): it *wraps* that type's
      rendering. It receives the base's rendered output as ``children`` — not the value — and
      composes around it (icon, badge, tracking wrapper, styling). Because it only sees the
      already-rendered output, it cannot bypass the base's behaviour (e.g. the built-in
      link/button URL sanitization). Multiple decorators compose in registration order.

    A renderer is simply the innermost/base decorator: it decorates the raw value into an
    element, and the wrappers decorate that. Only the base sees the value.

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

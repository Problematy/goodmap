Plugins
=======

Goodmap builds on platzky's plugin system and adds its own plugin ecosystem for the
map. A Goodmap plugin is an ordinary Python package that declares a ``goodmap.plugins``
entry point and ships a frontend component (served via Module Federation). Goodmap
registers this entry-point group and its own capability base classes with platzky at
startup, so Goodmap plugins are discovered, config-gated (``is_active``), and loaded
through platzky's normal plugin loader — see :doc:`platzky's plugin docs
<platzky:plugins>` for the underlying mechanism (``extra_plugin_bases`` /
``extra_plugins_entrypoints``).

Kinds of Goodmap frontend plugins
-------------------------------------

The capability a plugin provides determines *how* its frontend renders:

**Marker fields** (:class:`goodmap.plugin.MarkerFieldPluginBase`)
    Render a single location field inside a marker popup (capability ``"MarkerField"``,
    mounted by ``FieldRenderer``). A field plugin plays one of two roles, chosen by its
    ``config``:

    - **Renderer** (no ``config.decorates``): it *is* the component for the field ``type``
      matching its name — its shortcode transforms the value into ``{"type": "<name>", ...}``
      and it receives that value spread as props. The built-in field types ``hyperlink`` and
      ``CTA`` resolve the same way and take precedence over a plugin of the same name.
    - **Decorator** (``config.decorates`` set to a field ``type``): it *wraps* that type's
      rendering, receiving the base's rendered output as ``children`` (not the value) and
      composing around it (icon, badge, tracking wrapper, styling). Because it only sees the
      already-rendered output, it cannot bypass the base's behaviour, e.g. the built-in
      link/button URL sanitization. A renderer is simply the innermost/base decorator.

**Map overlays** (:class:`goodmap.plugin.MapOverlayPluginBase`)
    Render a component once *over the whole map*, not tied to any marker — e.g. a
    banner shown when no points are visible in the current view. Overlay components
    are mounted by ``MapOverlays``. They do not transform point/location data.

All kinds are discovered from the ``goodmap.plugins`` entry-point group. Each capability
exposes its React component under that capability's Module Federation module key —
``./MapOverlay`` for overlays and ``./MarkerField`` for field plugins (renderers and
decorators alike) — all served from the plugin's single ``remoteEntry.js``.

A single plugin may provide **several** capabilities by subclassing more than one base;
goodmap then emits one manifest entry per capability, each pointing at that capability's
module. See ``examples/plugins/silly-gif`` for a plugin that is both a map overlay *and* a marker
field renderer.

Map overlay plugins
-------------------

A map overlay subclasses :class:`~goodmap.plugin.MapOverlayPluginBase` and declares a
``goodmap.plugins`` entry point:

.. code-block:: python

    # my_overlay/plugin.py
    from typing import Any
    from goodmap.plugin import MapOverlayPluginBase

    class MyOverlayPlugin(MapOverlayPluginBase):
        """Show a banner over the map."""

        def __init__(self, config: dict[str, Any]) -> None:
            super().__init__(config)

.. code-block:: toml

    # pyproject.toml
    [tool.poetry.plugins."goodmap.plugins"]
    my_overlay = "my_overlay:MyOverlayPlugin"

The plugin's per-plugin ``config`` (from the database, see below) is delivered to the
React component as a ``config`` prop, so overlays are configurable without code
changes:

.. code-block:: jsx

    // frontend/src/MapOverlay.jsx  (exposed as "./MapOverlay")
    export default function MyOverlayPlugin({ config }) {
        return <div>{config.message}</div>;
    }

Goodmap serves the bundle at ``/plugins/<name>/static/remoteEntry.js`` and adds a manifest
entry ``{pluginName, url, module, capability, config}`` for each capability the plugin
provides. The ``capability`` token and its ``module`` are derived from the capability base
class name (``PluginBase`` stripped) —
:class:`~goodmap.plugin.MapOverlayPluginBase` (``"MapOverlay"`` / ``./MapOverlay``) and
:class:`~goodmap.plugin.MarkerFieldPluginBase` (``"MarkerField"`` / ``./MarkerField``) — and
the frontend uses ``capability`` to mount the component at the right place (overlays over the
map by ``MapOverlays``; field renderers and decorators in a marker by ``FieldRenderer``, which
tells them apart by ``config.decorates``).

Field renderers and ``visible_data``
------------------------------------

``visible_data`` is a list of field names displayed in location markers (see
:ref:`data-model-visible_data`). When a field is contributed by an active field-renderer
plugin, its shortcode transforms the value into ``{"type": "<name>", ...}`` and the
frontend renders the matching component (resolved by ``type``) in the marker popup.

Field decorator plugins
-----------------------

A decorator wraps an existing field renderer's output instead of replacing it — the way
to customize a built-in (``hyperlink``, ``CTA``) safely, since the base renderer still
runs. It is an ordinary :class:`~goodmap.plugin.MarkerFieldPluginBase` (there is no separate
decorator capability); setting ``config.decorates`` is what makes it act as a decorator
rather than a renderer. It needs no shortcode (it augments rendering, it does not produce
field values):

.. code-block:: python

    # hyperlink_badge/plugin.py
    from typing import Any
    from goodmap.plugin import MarkerFieldPluginBase

    class HyperlinkBadgePlugin(MarkerFieldPluginBase):
        def __init__(self, config: dict[str, Any]) -> None:
            super().__init__(config)

The React component receives the base renderer's rendered output as ``children`` (plus
its own ``config``) and composes around it. Because it only sees the already-rendered,
already-sanitized output, it cannot bypass the base renderer's behaviour:

.. code-block:: jsx

    // frontend/src/MarkerField.jsx  (exposed as "./MarkerField")
    export default function HyperlinkBadge({ config, children }) {
        return (
            <span className="hyperlink-badge">
                {children}
                {config.label && <sup> {config.label}</sup>}
            </span>
        );
    }

The field ``type`` a decorator wraps is set in its ``config`` via ``decorates`` (below).
Multiple decorators on the same type compose in registration order.

Configuration
-------------

Activate a plugin by adding it to the ``plugins`` object in your data source, keyed by
the entry-point name. The plugin loads only when ``is_active`` is ``true``; its
``config`` is passed to the plugin's ``__init__`` and (for frontend plugins) delivered
to the React component as the ``config`` prop:

.. code-block:: json

   {
     "plugins": {
       "nothingshere": {
         "is_active": true,
         "config": {
           "messages": {
             "pl": "Nie ma nic w pobliżu",
             "en": "Nothing nearby"
           }
         }
       }
     }
   }

A field-decorator plugin additionally sets ``decorates`` in its ``config`` to target the
field ``type`` it wraps:

.. code-block:: json

   {
     "plugins": {
       "hyperlink_badge": {
         "is_active": true,
         "config": { "decorates": "hyperlink", "label": "↗" }
       }
     }
   }

Each plugin defines its own ``config`` schema — refer to the plugin's documentation
for available fields.

After adding or removing a plugin, restart the Flask server.

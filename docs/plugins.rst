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
    mounted by ``FieldRenderer``). ``FieldRenderer`` renders a field as a **fold**: a *seed*
    (the built-in for the field ``type`` rendered from the value, e.g. ``hyperlink``/``CTA``,
    or a string when there is none), wrapped by every field plugin that attaches to that
    ``type``. A plugin's ``config`` declares which field it attaches to and where it sits:

    - ``field``: the field ``type`` it applies to. For a custom type, the plugin's platzky
      shortcode transforms the value into ``{"type": "<field>", ...}``.
    - ``order`` (optional): position in the stack — lower is more innermost; ties keep
      registration order.

    Every field plugin is the same kind of wrapper, receiving ``{ value, children, config }``.
    A **renderer** ignores ``children`` and renders from ``value``; a **decorator** composes
    around ``children`` (icon, badge, tracking wrapper). There is no separate role — the
    innermost plugin is simply the one whose ``children`` is the seed.

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
map by ``MapOverlays``; field plugins in a marker by ``FieldRenderer``, which folds them by
``config.field`` and ``config.order``).

Field renderers and ``visible_data``
------------------------------------

``visible_data`` is a list of field names displayed in location markers (see
:ref:`data-model-visible_data`). When a field is contributed by an active field-renderer
plugin, its shortcode transforms the value into ``{"type": "<name>", ...}`` and the
frontend renders the matching component (resolved by ``type``) in the marker popup.

Field plugins as decorators
---------------------------

A field plugin that wraps an existing field's rendering (rather than rendering the value
itself) is just an ordinary :class:`~goodmap.plugin.MarkerFieldPluginBase` that attaches to
that ``type`` — the way to customize a built-in (``hyperlink``, ``CTA``). It needs no
shortcode (it augments rendering, it does not produce field values):

.. code-block:: python

    # hyperlink_badge/plugin.py
    from typing import Any
    from goodmap.plugin import MarkerFieldPluginBase

    class HyperlinkBadgePlugin(MarkerFieldPluginBase):
        def __init__(self, config: dict[str, Any]) -> None:
            super().__init__(config)

The React component receives ``{ value, children, config }``. Acting as a decorator, it
composes around ``children`` (the current rendering) and ignores ``value``:

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

The plugin sets ``config.field`` to the type it attaches to (below) and, optionally,
``config.order`` for its position in the fold; higher order wraps further out.

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

A field plugin sets ``field`` in its ``config`` to the field ``type`` it attaches to (and,
optionally, ``order`` for its place in the fold):

.. code-block:: json

   {
     "plugins": {
       "hyperlink_badge": {
         "is_active": true,
         "config": { "field": "hyperlink", "order": 1, "label": "↗" }
       }
     }
   }

Each plugin defines its own ``config`` schema — refer to the plugin's documentation
for available fields.

After adding or removing a plugin, restart the Flask server.

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

Two kinds of Goodmap frontend plugins
-------------------------------------

The capability a plugin provides determines *how* its frontend renders:

**Field renderers** (:class:`goodmap.plugin.MarkerFieldPluginBase` + a platzky shortcode)
    Render a single location field inside a marker popup. The plugin's shortcode
    transforms the field value into ``{"type": "<name>", ...}`` on the backend; its
    frontend component (capability ``"field"``) is resolved by ``type`` and mounted by
    ``FieldRenderer``. The built-in field types ``hyperlink`` and ``CTA`` resolve through
    the same mechanism and take precedence over a plugin of the same name.

**Map overlays** (:class:`goodmap.plugin.MapOverlayPluginBase`)
    Render a component once *over the whole map*, not tied to any marker — e.g. a
    banner shown when no points are visible in the current view. Overlay components
    are mounted by ``MapOverlays``. They do not transform point/location data.

Both kinds are discovered from the ``goodmap.plugins`` entry-point group and must
expose their React component under the Module Federation key ``./Plugin`` (the module
name Goodmap requests from each plugin's ``remoteEntry.js``).

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

    // frontend/src/Plugin.jsx  (exposed as "./Plugin")
    export default function MyOverlayPlugin({ config }) {
        return <div>{config.message}</div>;
    }

Goodmap serves the bundle at ``/plugins/<name>/static/remoteEntry.js`` and adds a
manifest entry ``{pluginName, url, module: "./Plugin", capability, config}``. Each
Goodmap capability base class declares its own ``capability`` value —
:class:`~goodmap.plugin.MapOverlayPluginBase` declares ``"overlay"`` and
:class:`~goodmap.plugin.MarkerFieldPluginBase` declares ``"field"`` — and the frontend
uses it to mount the component at the right place (overlays over the map by
``MapOverlays``; field renderers in a marker by ``FieldRenderer``).

Field renderers and ``visible_data``
------------------------------------

``visible_data`` is a list of field names displayed in location markers (see
:ref:`data-model-visible_data`). When a field is contributed by an active field-renderer
plugin, its shortcode transforms the value into ``{"type": "<name>", ...}`` and the
frontend renders the matching component (resolved by ``type``) in the marker popup.

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

Each plugin defines its own ``config`` schema — refer to the plugin's documentation
for available fields.

After adding or removing a plugin, restart the Flask server.

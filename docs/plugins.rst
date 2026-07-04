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

The capability a plugin subclasses determines *how* its frontend renders:

**Field renderers** (``platzky.plugin.ContentTransformerPluginBase`` + shortcodes)
    Render a single location field inside a marker popup. When a plugin-contributed
    field appears in a location's ``visible_data`` and the plugin is active, the API
    wraps the field value as ``{"scope": "<shortcode_name>", ...}``; the frontend
    detects the ``scope`` key and mounts the plugin component there (``PluginSlot``).

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
manifest entry ``{scope, url, module: "./Plugin", kind, config}``. ``kind`` is
``"overlay"`` for :class:`~goodmap.plugin.MapOverlayPluginBase` plugins and ``"field"``
otherwise; the frontend uses it to route overlays to ``MapOverlays`` and field
renderers to ``PluginSlot``.

Field renderers and ``visible_data``
------------------------------------

``visible_data`` is a list of field names displayed in location markers (see
:ref:`data-model-visible_data`). When a field is contributed by an active field-renderer
plugin, the API wraps its value with ``{"scope": "<shortcode_name>", ...}`` and the
frontend renders the matching plugin component in the marker popup.

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

If a field-renderer plugin is removed from the configuration while a location still
has fields referencing it, those fields are silently dropped from the API response. A
debug message is logged:

.. code-block:: text

   DEBUG:goodmap.formatter:Dropping field 'promocode': unconfigured plugin data ...

To see these messages, enable debug logging:

.. code-block:: bash

   export FLASK_DEBUG=1

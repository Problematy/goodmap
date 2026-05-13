Plugins
=======

Goodmap supports platzky plugins — standalone Python packages that extend
functionality via shortcodes and module federation frontend components.
Plugins are written against platzky's shortcode system and are not aware of
locations; Goodmap maps shortcode names to location field renderers automatically.

Overview
--------

Plugins are discovered automatically through Python entry points
(``platzky.plugins`` group). Each plugin can:

* Register shortcodes for blog/content rendering
* Expose a React component via Module Federation
* Provide static assets served by the Flask backend

Goodmap then uses the registered shortcode names as field renderer identifiers
for locations. ``visible_data`` is a list of field names that should be
displayed in location markers on the map. When a plugin-contributed field
appears in a location's ``visible_data`` and the plugin is configured, the API
wraps the field value with ``{"scope": "<shortcode_name>", ...}``. The frontend
detects the ``scope`` key and renders the appropriate plugin component.

Configuration
-------------

Add the plugin entry to the ``plugins`` list in your data source (e.g.
``data.json``):

.. code-block:: json

   {
     "plugins": [
       {
         "name": "promocode",
         "config": {
           "text": "Reveal your discount",
           "color": "#e63946"
         }
       }
     ]
   }

Each plugin has its own configuration schema — refer to the plugin's
documentation for available fields.

After adding or removing a plugin, restart the Flask server.

If a plugin is removed from the configuration while a location still has
fields referencing it, those fields are silently dropped from the API
response. A debug message is logged:

.. code-block:: text

   DEBUG:goodmap.formatter:Dropping field 'promocode': unconfigured plugin data ...

To see these messages, enable debug logging:

.. code-block:: bash

   export FLASK_DEBUG=1

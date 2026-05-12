Plugins
=======

Goodmap supports platzky plugins — standalone Python packages that extend
functionality via shortcodes, custom location field renderers, and module
federation frontend components.

Overview
--------

Plugins are discovered automatically through Python entry points
(``platzky.plugins`` group). Each plugin can:

* Register shortcodes for blog/content rendering
* Expose a React component via Module Federation for rendering inside map
  popups
* Provide static assets served by the Flask backend

When a plugin-contributed field appears in a location's ``visible_data`` and
the plugin is configured, the API wraps the field value with
``{"scope": "<shortcode_name>", ...}``. The frontend detects the ``scope``
key and renders the appropriate plugin component.

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



Architecture
------------

Field Resolution Flow
~~~~~~~~~~~~~~~~~~~~~

1. Application starts in ``goodmap.py:create_app_from_config()``:
   * Platzky loads plugins configured in the database via ``plugify()``
   * Each ``ContentTransformerPluginBase`` subclass registers its shortcodes
     in ``app.shortcodes``
   * ``field_renderers`` is auto-populated from ``app.shortcodes``::

       for sc_name in app.shortcodes:
           field_renderers.setdefault(sc_name, sc_name)

2. When a location's ``visible_data`` includes a field matching a shortcode
   name, ``formatter.py:_apply_field_plugin()`` wraps it:

   * If the field name is in ``field_renderers``:
     ``{"scope": "<shortcode>", ...original fields...}``
   * If the value is a ``dict`` with a ``code`` key, it is base64-encoded
     for safe transport
   * If the field name is NOT in ``field_renderers``, the value is a ``dict``
     with a ``code`` key but no ``type``/``scope`` — it is treated as
     unconfigured plugin data and dropped (with a debug log)

3. The frontend receives the wrapped value and renders:

   * ``mapCustomTypeToReactComponent`` checks for ``customValue.scope``
   * Delegates to ``<PluginSlot scope={scope} props={props} />``
   * ``PluginSlot`` looks up the registered component in the plugin registry
     and renders it with the remaining props

Module Federation
~~~~~~~~~~~~~~~~~

Plugin frontend components are loaded as Webpack 5 Module Federation remotes:

1. The backend discovers plugin entry points and registers Flask blueprints
   to serve each plugin's ``static/`` directory
2. A ``PLUGIN_MANIFEST`` is embedded in ``map.html`` as
   ``window.PLUGIN_MANIFEST``
3. The frontend's ``pluginLoader.js`` reads the manifest, loads each remote,
   initialises the shared scope, and registers the component with the
   ``pluginRegistry``
4. ``PluginSlot`` subscribes to registry changes and re-renders once the
   component is available

CORS headers (``Access-Control-Allow-Origin: *``) are set on plugin static
blueprints to allow the frontend dev server to fetch the remote entry.

Field Lifecycle
---------------

+----------------------+-----------------------------------------------+--------------------------------------------+
| Scenario             | API Response                                  | Frontend Behaviour                         |
+======================+===============================================+============================================+
| Plugin configured    | ``{"scope": "promocode", "code": "BASE64",   | ``PluginSlot`` renders MF component        |
|                      |   "text": "...", "color": "#..."}``           |                                            |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Plugin NOT           | Field omitted from response, debug log        | Field not displayed at all                 |
| configured           | written                                       |                                            |
+----------------------+-----------------------------------------------+--------------------------------------------+
| Standard custom type | ``{"type": "hyperlink", "value": "..."}``     | Rendered as link or CTA button             |
+----------------------+-----------------------------------------------+--------------------------------------------+

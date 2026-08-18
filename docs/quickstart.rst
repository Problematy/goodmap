Quickstart
==========

Build a working map from an empty directory. You will write two files — a data source
and a config — and run one command.

The example is a map of bridges in Wrocław, filterable by who may cross them and by
whether they are free to use.

Before you start, install Goodmap (:doc:`installation`):

.. code-block:: bash

   pip install goodmap

.. _quickstart-data:

1. Write the data source
------------------------

Create ``data.json``. This one file holds both the points and the map's schema:

.. code-block:: json

   {
     "map": {
       "data": [
         {
           "uuid": "9264286a-5d33-4e38-ab11-c8e179a7754a",
           "name": "Grunwaldzki",
           "position": [51.109444, 17.0525],
           "type_of_place": "big bridge",
           "accessible_by": ["pedestrians", "cars"],
           "is_free": "true"
         },
         {
           "uuid": "c8ecf476-5968-40da-ba5c-e810ad9ff203",
           "name": "Zwierzyniecka",
           "position": [51.108056, 17.07],
           "type_of_place": "small bridge",
           "accessible_by": ["bikes", "pedestrians"],
           "is_free": "true"
         },
         {
           "uuid": "1a8f9a2e-4b6d-4a1a-9a8e-2f6c7d0b3e9a",
           "name": "Milenijny",
           "position": [51.133692, 16.993103],
           "type_of_place": "big bridge",
           "accessible_by": ["cars"],
           "is_free": "false"
         }
       ],
       "location_obligatory_fields": [
         ["name", "str"],
         ["type_of_place", "str"],
         ["accessible_by", "list"],
         ["is_free", "str"]
       ],
       "categories": {
         "accessible_by": ["bikes", "cars", "pedestrians"],
         "type_of_place": ["big bridge", "small bridge"],
         "is_free": ["true", "false"]
       },
       "categories_filter_mode": {
         "is_free": "boolean"
       },
       "visible_data": ["accessible_by", "type_of_place", "is_free"],
       "meta_data": ["uuid"],
       "reported_issue_types": ["under construction", "has a hole", "other"]
     },
     "site_content": {
       "home_page_path": "/map",
       "pages": [],
       "menu_items": {},
       "logo_url": "",
       "primary_color": "#FFFFFF",
       "secondary_color": "#245466"
     }
   }

What each part does:

``data``
   The points. Every point needs a ``uuid``, a ``position`` as
   ``[latitude, longitude]``, a ``name`` (the popup title), and a ``type_of_place``
   (the popup subtitle). Anything else is yours to invent.

``location_obligatory_fields``
   The fields beyond ``uuid`` and ``position`` that every point must have. Goodmap
   validates against this and builds the "suggest a new point" form from it.

``categories``
   The filterable fields, each with its list of allowed values. These become the filter
   checkboxes in the left panel.

``categories_filter_mode``
   How multiple checked values in one category combine. ``boolean`` renders
   ``is_free`` as a single "free only" checkbox instead of a true/false pair. Five modes
   are available — see :ref:`categories-filter-mode`.

``visible_data``
   Which fields show inside the marker popup. Fields not listed here are never sent to
   the frontend.

``site_content``
   platzky's section — pages, menus, colours. ``home_page_path: "/map"`` is what makes
   ``/`` serve the map; without it, ``/`` is platzky's own homepage and the map lives at
   ``/map`` only.

The full reference for this file is :doc:`data-source`.

2. Write the config
-------------------

Create ``config.yml`` next to it:

.. code-block:: yaml

   APP_NAME: Bridges in Wrocław
   SECRET_KEY: change-me-before-production
   USE_WWW: False

   LANGUAGES:
     en:
       name: English
       flag: gb
       country: GB

   DB:
     TYPE: json_file
     PATH: data.json

   FEATURE_FLAGS:
     USE_LAZY_LOADING: true
     SHOW_SEARCH_BAR: true
     SHOW_SUGGEST_NEW_POINT_BUTTON: true

``DB`` points at the data source you just wrote. ``FEATURE_FLAGS`` switch optional
behaviour on and off — every flag is listed in :ref:`config-feature-flags`.

.. important::

   ``USE_WWW: False`` matters locally. It defaults to true, which redirects every request
   to the ``www.`` hostname — so on ``localhost`` you get a ``301`` to
   ``http://www.localhost/`` and nothing loads. Turn it back on in production if you serve
   from a ``www.`` domain.

.. warning::

   ``SECRET_KEY`` signs session cookies and CSRF tokens. Use a real random value in
   production and keep it out of version control — see :ref:`deployment-secrets`.

3. Run it
---------

.. code-block:: bash

   flask --app "goodmap.goodmap:create_app(config_path='config.yml')" --debug run

Open http://localhost:5000/ — three bridges on a map, an "accessible by" filter, and a
"free only" checkbox in the left panel. Clicking a marker shows who may cross it and
whether it is free.

.. note::

   ``--debug`` reloads on change and shows tracebacks. Drop it outside development, and
   see :doc:`deployment` for how to serve this properly.

4. Talk to the API
------------------

The same data is available as JSON. Filters are query parameters — repeat a parameter to
check several boxes:

.. code-block:: bash

   curl 'http://localhost:5000/api/locations'
   curl 'http://localhost:5000/api/locations?accessible_by=bikes'
   curl 'http://localhost:5000/api/locations?accessible_by=bikes&accessible_by=cars'

``/api/locations`` returns only identity and position — the popup contents are a second
call, so a map with thousands of points stays cheap:

.. code-block:: bash

   curl 'http://localhost:5000/api/location/c8ecf476-5968-40da-ba5c-e810ad9ff203'

Sorting by distance and capping the result set, for a "near me" view:

.. code-block:: bash

   curl 'http://localhost:5000/api/locations?lat=51.11&lon=17.03&limit=5'

Every endpoint is documented in :doc:`http-api`, and the running app serves its own
OpenAPI schema at http://localhost:5000/api/doc.

5. Change something
-------------------

Add another bridge, or add a new filterable field:

1. Add the field to a point in ``data.json``.
2. Add it to ``categories`` with its allowed values, so it becomes filterable.
3. Add it to ``visible_data``, so it shows in the popup.
4. Add it to ``location_obligatory_fields`` if every point must have it.
5. Restart the server.

With ``TYPE: json_file`` the file is re-read per request, so data edits show up on
refresh — but the schema keys above are read once at startup, so changing them needs a
restart.

Where to go next
----------------

- :doc:`configuration` — every ``config.yml`` key and feature flag.
- :doc:`data-source` — the full data format, all five filter modes, and the Google Cloud
  Storage and MongoDB backends.
- :doc:`deployment` — running it for real.

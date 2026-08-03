Quickstart
==========

Build a working map from an empty directory. You will write two files — a data source
and a config — and run one command.

The example is a map of climbing crags, filterable by rock type and by whether the
approach is wheelchair-accessible.

Before you start, install Goodmap (:doc:`installation`):

.. code-block:: bash

   pip install --pre goodmap

.. _quickstart-data:

1. Write the data source
------------------------

Create ``data.json``. This one file holds both the points and the map's schema:

.. code-block:: json

   {
     "map": {
       "data": [
         {
           "uuid": "5f9e1a3c-2b4d-4e6f-8a91-0c2d4e6f8a91",
           "name": "Kobylany",
           "position": [50.1655, 19.7420],
           "type_of_place": "limestone crag",
           "rock": "limestone",
           "wheelchair_approach": "false"
         },
         {
           "uuid": "7c3d5e7f-9a1b-4c3d-8e5f-7a9b1c3d5e7f",
           "name": "Zakrzówek",
           "position": [50.0397, 19.9060],
           "type_of_place": "limestone crag",
           "rock": "limestone",
           "wheelchair_approach": "true"
         },
         {
           "uuid": "9b1c3d5e-7f9a-4b1c-8d5e-9f1a3b5c7d9e",
           "name": "Rudawy Janowickie",
           "position": [50.8330, 15.9170],
           "type_of_place": "granite crag",
           "rock": "granite",
           "wheelchair_approach": "false"
         }
       ],
       "location_obligatory_fields": [
         ["name", "str"],
         ["type_of_place", "str"],
         ["rock", "str"]
       ],
       "categories": {
         "rock": ["limestone", "granite", "sandstone"],
         "wheelchair_approach": ["true", "false"]
       },
       "categories_filter_mode": {
         "wheelchair_approach": "boolean"
       },
       "visible_data": ["rock", "wheelchair_approach"],
       "meta_data": ["uuid"],
       "reported_issue_types": ["overgrown", "access banned", "other"]
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
   ``wheelchair_approach`` as a single "accessible only" checkbox instead of a
   true/false pair. Five modes are available — see :ref:`categories-filter-mode`.

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

   APP_NAME: Crags
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

Open http://localhost:5000/ — three crags on a map, a rock-type filter, and an
"accessible only" checkbox in the left panel. Clicking a marker shows its rock type and
approach.

.. note::

   ``--debug`` reloads on change and shows tracebacks. Drop it outside development, and
   see :doc:`deployment` for how to serve this properly.

4. Talk to the API
------------------

The same data is available as JSON. Filters are query parameters — repeat a parameter to
check several boxes:

.. code-block:: bash

   curl 'http://localhost:5000/api/locations'
   curl 'http://localhost:5000/api/locations?rock=granite'
   curl 'http://localhost:5000/api/locations?rock=granite&rock=limestone'

``/api/locations`` returns only identity and position — the popup contents are a second
call, so a map with thousands of points stays cheap:

.. code-block:: bash

   curl 'http://localhost:5000/api/location/7c3d5e7f-9a1b-4c3d-8e5f-7a9b1c3d5e7f'

Sorting by distance and capping the result set, for a "near me" view:

.. code-block:: bash

   curl 'http://localhost:5000/api/locations?lat=50.06&lon=19.94&limit=5'

Every endpoint is documented in :doc:`http-api`, and the running app serves its own
OpenAPI schema at http://localhost:5000/api/doc.

5. Change something
-------------------

Add ``sandstone`` crags, or add a new filterable field:

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

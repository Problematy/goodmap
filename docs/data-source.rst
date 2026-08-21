The data source
===============

The data source is where the map itself lives: the points, which of their fields are
shown, which are filterable, and which plugins are active. It is separate from
``config.yml`` (:doc:`configuration`), which only says *how the app runs*.

Whatever backend you choose, the shape is the same — a ``map`` section holding the points
and their schema, alongside platzky's ``site_content`` section:

.. code-block:: text

   {
     "map": {
       "data": [ ... ],
       "location_obligatory_fields": [ ... ],
       "categories": { ... },
       "visible_data": [ ... ],
       "meta_data": [ ... ],
       "reported_issue_types": [ ... ],
       "suggestions": [ ... ],
       "reports": [ ... ]
     },
     "plugins": { ... },
     "site_content": { ... }
   }

Note that ``plugins`` is a **sibling** of ``map``, not a key inside it.

Only ``data`` is structurally required. ``categories`` defaults to no categories
if omitted (a map with only plain, unfiltered points is a valid setup); ``suggestions``
and ``reports`` are created by the app as users submit things.

Points
------

``data`` is the list of points. Each one is a free-form object with five fields Goodmap
treats specially — everything else in the example below, such as ``accessible_by``, is an
ordinary field of your own:

.. code-block:: json

   {
     "uuid": "9264286a-5d33-4e38-ab11-c8e179a7754a",
     "name": "Grunwaldzki",
     "position": [51.1095, 17.0525],
     "type_of_place": "big bridge",
     "accessible_by": ["pedestrians", "cars"],
     "remark": "closed for renovation"
   }

``uuid`` (required)
   The point's identity, used in ``/api/location/<uuid>``. **It must
   be a real UUID**.

``position`` (required)
   ``[latitude, longitude]``, in that order. Latitude is validated to −90..90 and
   longitude to −180..180.

``name`` (required in practice)
   Used as the marker popup's **title**.

``type_of_place`` (required in practice)
   Used as the marker popup's **subtitle**.

``remark`` (optional)
   Free text. Its presence — not its content — is exposed by ``/api/locations`` as
   ``marker.badge: true`` (see :ref:`data-source-marker-styles`), so the frontend can
   flag points that have something noteworthy without fetching them all.

Everything else is yours. Custom fields are only *shown* if you list them in
``visible_data``, and only *filterable* if you list them in ``categories``.

.. note::

   ``name`` and ``type_of_place`` are not formally part of the base model, but the popup
   formatter reads both unconditionally, so a point missing either will fail to render.
   Treat them as mandatory and declare them in ``location_obligatory_fields``.

Field schema
------------

.. _data-model-location_obligatory_fields:

``location_obligatory_fields``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A list of ``[field_name, field_type]`` pairs listing the fields — beyond the built-in
``uuid`` and ``position`` — that every point must have:

.. code-block:: json

   {
     "location_obligatory_fields": [
       ["name", "str"],
       ["type_of_place", "str"],
       ["accessible_by", "list"]
     ]
   }

Supported types: ``str``, ``list``, ``int``, ``float``, ``bool``, ``dict``.

The key itself is optional — leave it out and it is treated as an empty list, so nothing
beyond ``uuid`` and ``position`` is required and the suggest form has no fields.

This drives three things at once:

- **Validation.** Points submitted through ``/api/suggest-new-point`` are rejected with
  ``400`` if a field is missing or has a value outside its category's allowed list.
- **The suggest-a-point form.** The frontend generates its fields from this schema.
- **Length limits.** String fields are capped at 200 characters, lists at 20 items of at
  most 100 characters each.

.. _data-model-visible_data:

``visible_data`` and ``meta_data``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "visible_data": ["remark", "accessible_by", "type_of_place"],
     "meta_data": ["uuid"]
   }

``visible_data``
   Field names shown in the marker popup's body, in the order given.

``meta_data``
   Field names returned in the popup's separate ``metadata`` object, for data that is
   needed but not part of the visible body — typically ``uuid``.

**Together the two lists are a privacy boundary**: ``/api/location/<uuid>`` returns a
field only if it appears in one of them, so internal fields can live in the data without
reaching the frontend. Note that it really is *either* list — a field in ``meta_data`` is
returned even though it is not in ``visible_data``. Leaving a field out of
``visible_data`` alone does not hide it.

Both are translated through gettext before being returned (:ref:`config-translations`).

Categories and filtering
------------------------

``categories`` maps a field name to the list of values it may take. Each category becomes
a group of filter controls in the left panel, one per value:

.. code-block:: json

   {
     "categories": {
       "accessible_by": ["bikes", "cars", "pedestrians"],
       "type_of_place": ["big bridge", "small bridge"]
     }
   }

Categories do double duty: they define the filters **and** constrain what values the
matching field may hold, so a point with ``"accessible_by": ["boats"]`` is rejected.

Filtering happens through query parameters — one parameter per checked box, repeated:

.. code-block:: text

   /api/locations?accessible_by=bikes&accessible_by=cars&type_of_place=big%20bridge

Across categories, selections always combine with **AND**: a point must satisfy every
category that has an active selection. Within one category, how the checked values
combine is up to you.

.. _categories-filter-mode:

Filter modes
~~~~~~~~~~~~

``categories_filter_mode`` maps a category to how *multiple selected values within it*
combine. Categories not listed default to ``"or"``.

``"or"`` (default)
   A point matches if it has **any** of the selected values — the usual "check more boxes
   to broaden results" behaviour. Checking both ``bikes`` and ``cars`` shows points that
   allow bikes *or* cars, rather than only those allowing both (which is often nothing).

``"and"``
   A point matches only if it has **every** selected value — narrowing rather than
   broadening. Only meaningful for list-valued categories, where a point can hold several
   values at once: an ``amenities`` field where checking ``lighting`` and ``benches``
   should show only places with both. Still rendered as checkboxes, with a "(match all)"
   hint on the category title so it reads differently from the default.

``"exclusive"``
   Single-select: rendered as **radio buttons**, so only one value can be active. Use it
   for three or more mutually exclusive states, e.g. a toll tier of ``free`` /
   ``discounted`` / ``full_price``.

``"boolean"``
   For a field with exactly the two values ``"true"`` and ``"false"``. Only the ``"true"``
   option is rendered, as a single checkbox — leaving it unchecked already means "show
   everything", so there is no separate control for isolating ``"false"``. Use it when
   nobody would deliberately filter for the negative case: a "free only" checkbox on an
   ``is_free`` field, since drivers want "free" or "all", not "paid only".

``"threshold"``
   For an ordered, numeric-valued category such as a speed limit. Selecting a value
   matches every point whose value is **at or below** the highest selected one —
   selecting ``30`` also matches ``10``, but not ``50``. Rendered as radio buttons, since
   selecting more than one would be redundant: the highest selection alone sets the
   cutoff.

.. _data-source-help:

Defaults and help text
~~~~~~~~~~~~~~~~~~~~~~

``categories_default_checked``
   Category → the option values pre-checked when the app first loads, before the user
   touches anything. Values that are not in the category's allowed list are ignored.

``categories_help``
   The list of categories that get a help tooltip next to the category title. The text
   comes from the translation key ``categories_help_<category>``.

``categories_options_help``
   Category → the option values that get a help tooltip. The text comes from the
   translation key ``categories_options_help_<option>``.

Both help keys are ignored unless the ``CATEGORIES_HELP`` feature flag is on.

Putting it together
~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "categories": {
       "accessible_by": ["bikes", "cars", "pedestrians"],
       "type_of_place": ["big bridge", "small bridge"],
       "is_free": ["true", "false"],
       "speed_limit": ["10", "30", "50"],
       "amenities": ["lighting", "benches", "toilets"]
     },
     "categories_filter_mode": {
       "accessible_by": "or",
       "type_of_place": "exclusive",
       "is_free": "boolean",
       "speed_limit": "threshold",
       "amenities": "and"
     },
     "categories_default_checked": {
       "accessible_by": ["cars"]
     },
     "categories_help": ["accessible_by"],
     "categories_options_help": {
       "accessible_by": ["cars", "pedestrians"]
     }
   }

Each category's active mode is exposed as ``filter_mode`` in the
``/api/categories-full`` response, so a custom frontend can render the right control —
checkbox or radio — without hardcoding category names.

.. _data-source-marker-styles:

Marker styles
-------------

``marker_styles`` picks which of your fields drive each point's pin icon and color, and
supplies the lookup tables those values are resolved through. It is entirely optional —
a map with no ``marker_styles`` still renders, just with plain pins.

.. code-block:: json

   {
     "marker_styles": {
       "icon_field": "type_of_place",
       "color_field": "transparency",
       "icons": {
         "big bridge": "https://cdn.example.com/bridge.svg",
         "container": {"provider": "phosphor", "value": "shipping-container"}
       },
       "colors": {
         "lacking": "#c62828",
         "full": "#2e7d32"
       }
     }
   }

``icon_field``, ``color_field``
   Names of fields on your points whose *value* selects the icon/color for that point.
   Either or both may be omitted.

   Each must be declared in :ref:`data-model-location_obligatory_fields` — a field
   every point is guaranteed to have, so that styling is never driven by something
   only some of your points carry. A name that isn't declared there is ignored, and
   pins get no icon/color from it.

``icons``
   Maps a value of ``icon_field`` to either a plain URL string, or
   ``{"provider": "phosphor", "value": "<icon-name>"}`` to use a `Phosphor
   <https://phosphoricons.com/>`_ icon by name instead of hosting your own SVG.
   ``{"provider": "url", "value": "..."}`` is the plain string spelled out explicitly.

   ``phosphor`` and ``url`` are the providers GoodMap knows; each one's URL is built
   server-side, so the browser only ever receives finished URLs and a new provider needs
   no frontend release. An entry GoodMap cannot make sense of — an unknown ``provider``,
   a missing ``value`` — is logged as a warning at startup and left out, costing that one
   pin its icon rather than breaking the map.

``colors``
   Maps a value of ``color_field`` to a CSS color.

A point whose ``icon_field``/``color_field`` value has no entry in ``icons``/``colors``
simply renders without that part of the styling — this is not an error. A point with a
``remark`` (see above) always gets the asterisk badge regardless of whether its icon/color
matched anything.

User submissions
----------------

``reported_issue_types``
~~~~~~~~~~~~~~~~~~~~~~~~

The list of problems a visitor may report against a point, offered as choices in the
report form:

.. code-block:: json

   {
     "reported_issue_types": ["under construction", "has a hole", "other"]
   }

``/api/report-location`` rejects a description that is not in this list — **unless**
``"other"`` is one of the options, in which case free text up to 500 characters is
accepted too. Include ``"other"`` if you want to hear about problems you did not
anticipate; leave it out to keep reports strictly categorised.

``suggestions`` and ``reports``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Written by the app, not by you. A point submitted through ``/api/suggest-new-point``
lands in ``suggestions`` with ``"status": "pending"``; a problem reported through
``/api/report-location`` lands in ``reports`` with ``"status": "pending"`` and
``"priority": "medium"``. Neither affects the live map: nothing in ``suggestions`` or
``reports`` is served to visitors, and a suggested point only appears on the map once you
move it into ``data`` yourself.

.. _data-source-plugins:

``plugins``
-----------

**Every plugin is activated here, and only here** — Goodmap's own (map overlays and
marker-field renderers) and platzky's (notifiers and the like) alike. ``config.yml`` has
no say in it.

This is a **top-level key**, alongside ``map`` and ``site_content`` — not inside ``map``.
Put it in the wrong place and nothing complains: the app starts, the plugin is simply
never loaded.

.. code-block:: json

   {
     "plugins": {
       "nothingshere": {
         "is_active": true,
         "config": { "messages": { "en": "Nothing nearby", "pl": "Nie ma nic w pobliżu" } }
       }
     }
   }

Entries are keyed by the plugin's **entry-point name**, which is the name its package
registers under ``goodmap.plugins`` or ``platzky.plugins`` — not the distribution name you
``pip install``. Each entry takes ``is_active`` (default ``false``) and ``config``, whose
contents are the plugin's own business.

A named plugin that is active but not installed is a **startup error**, not a warning, so
a typo in the key stops the app rather than silently disabling a feature. An entry with
``"is_active": false`` is skipped without being resolved.

See :doc:`plugins` for writing one, and restart the app after changing this key.

``site_content``
----------------

platzky's half of the file: pages, menu items, logo, fonts and colours. Goodmap only
depends on one key of it:

.. code-block:: json

   {
     "site_content": {
       "home_page_path": "/map",
       "pages": [],
       "menu_items": {},
       "logo_url": "",
       "primary_color": "#FFFFFF",
       "secondary_color": "#245466"
     }
   }

The map view is registered at ``/map``, because platzky reserves ``/`` for its own
homepage dispatch. Setting ``home_page_path`` to ``"/map"`` makes ``/`` serve the map
directly, with no redirect. Leave it out and visitors get platzky's homepage instead, with
the map reachable only at ``/map``.

.. _data-source-backends:

Backends
--------

Choose with the ``DB`` key in ``config.yml`` (:ref:`config-db`).

JSON file
~~~~~~~~~

.. code-block:: yaml

   DB:
     TYPE: json_file
     PATH: data.json

The whole structure above in one file on disk. Read per request, so edits to ``data``
show up on the next refresh — though the schema keys (``categories``,
``location_obligatory_fields``, ``visible_data``) are read once at startup and need a
restart. Writes — new suggestions and reports — are written back atomically via a
temporary file and a rename, so a crash mid-write cannot truncate your data.

Best for: development, and small-to-medium read-mostly maps served by a single process.
Not suitable for multiple worker processes writing concurrently — see
:ref:`deployment-workers`.

Google Cloud Storage
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   DB:
     TYPE: google_json
     BUCKET_NAME: good-map
     SOURCE_BLOB_NAME: data.json

The same JSON structure, read from a bucket blob. Authentication uses standard Google
application default credentials.

.. warning::

   **This backend is read-only.** Adding a location, updating a report, deleting a
   suggestion — all silently do nothing. Suggestions submitted by visitors are accepted by
   the API but never persisted. Use it for maps whose data is published from elsewhere,
   not for maps that accept user submissions.

MongoDB
~~~~~~~

Points live in a ``locations`` collection, suggestions in ``suggestions``, reports in
``reports``, and everything else — ``categories``, ``visible_data``, ``meta_data``,
``location_obligatory_fields``, ``categories_filter_mode``, ``reported_issue_types`` — in
a single configuration document in the ``config`` collection with ``_id:
"map_config"``:

.. code-block:: javascript

   db.config.insertOne({
     _id: "map_config",
     categories: { accessible_by: ["bikes", "cars", "pedestrians"] },
     categories_filter_mode: { speed_limit: "threshold" },
     visible_data: ["accessible_by", "type_of_place"],
     meta_data: ["uuid"],
     location_obligatory_fields: [["name", "str"], ["type_of_place", "str"]],
     reported_issue_types: ["under construction", "other"]
   })

Filtering, sorting and pagination are pushed down into the query rather than done in
Python, so this is the backend that scales. Filter modes translate to Mongo operators:
``or``/``exclusive``/``boolean`` become ``$in``, ``and`` becomes ``$all``, and
``threshold`` becomes ``$lte`` — which means **threshold fields must be stored as
numbers**, not strings, for that mode to match.

Best for: large datasets, concurrent writes, or more than one worker process.

Validating your data
--------------------

Points are validated when they are read, so a malformed file fails at request time. To
catch problems before deploying, validate the file against the schema it declares:

.. code-block:: python

   """Validate a Goodmap JSON data file. Usage: python validate_data.py data.json"""
   import json
   import sys

   from goodmap.data_models.location import create_location_model
   from goodmap.exceptions import LocationValidationError

   raw = json.load(open(sys.argv[1]))["map"]
   model = create_location_model(
       raw.get("location_obligatory_fields", []),
       raw.get("categories", {}),
   )

   failures = 0
   for point in raw["data"]:
       try:
           model.model_validate(point)
       except LocationValidationError as error:
           failures += 1
           uuid = point.get("uuid", "<no uuid>")
           for detail in error.validation_errors:
               field = ".".join(str(part) for part in detail["loc"]) or "<point>"
               print(f"{uuid}: {field}: {detail['msg']}")

   print(f"{len(raw['data'])} points checked, {failures} invalid")
   sys.exit(1 if failures else 0)

This catches missing obligatory fields, values outside a category's allowed list, and
out-of-range coordinates, and reports the offending field for each one::

   22222222-2222-2222-2222-222222222222: name: Field required
   33333333-3333-3333-3333-333333333333: type_of_place: Value error, must be one of ...

.. note::

   Read the failures off ``error.validation_errors``, not off the exception itself.
   ``LocationValidationError`` prints as a bare ``Validation failed for location
   '<uuid>'`` — it withholds detail on purpose, so that API responses never leak the
   shape of your data.

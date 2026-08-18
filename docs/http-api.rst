HTTP API
========

Everything the map UI does, it does through this API — so anything the UI can do, your own
client can do too. All responses are JSON.

A running instance also serves its own generated OpenAPI schema:

.. list-table::
   :widths: 40 60

   * - ``/api/doc``
     - index of the formats below
   * - ``/api/doc/swagger/``
     - Swagger UI
   * - ``/api/doc/redoc/``
     - ReDoc
   * - ``/api/doc/openapi.json``
     - raw OpenAPI document

Use this page for the semantics and the schema endpoint for the exact shapes of the
release you are running.

Conventions
-----------

**Filters are repeated query parameters.** One parameter per checked value:
``?accessible_by=bikes&accessible_by=cars``. Which parameters are valid depends entirely
on the ``categories`` in your data source (:doc:`data-source`).

**Writes need a CSRF token.** CSRF protection is on for the whole app, so ``POST``,
``PUT`` and ``DELETE`` without a token get ``400 The CSRF token is missing``. Send it as
an ``X-CSRFToken`` header. Server-rendered pages expose one in a meta tag:

.. code-block:: html

   <meta name="csrf-token" content="...">

.. code-block:: javascript

   const token = document.querySelector('meta[name="csrf-token"]').content;
   await fetch('/api/report-location', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
       body: JSON.stringify({ id: locationUuid, description: 'has a hole' }),
   });

**Errors are ``{"message": "..."}``**, occasionally with an extra ``error`` field.
Messages are deliberately generic — the details go to the server log, not the response.

**Strings are translated** to the request's language before being returned, so category
keys and field names come back as display text (:ref:`config-translations`).

Reading the map
---------------

.. _api-locations:

``GET /api/locations``
~~~~~~~~~~~~~~~~~~~~~~

The points to draw, filtered. Returns identity and position only — deliberately, so a map
with thousands of points is cheap to load. Popup contents come from
:ref:`api-location-detail` when a marker is clicked.

Query parameters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Parameter
     - Meaning
   * - *category name*
     - Filter value; repeat for several. Combined per :ref:`categories-filter-mode`.
   * - ``lat``, ``lon``
     - Sort results by distance from this coordinate, nearest first. Both required, or
       neither applies.
   * - ``limit``
     - Return at most this many points. Applied after sorting, so ``lat``/``lon``/``limit``
       together give "the N nearest".

.. code-block:: bash

   curl 'http://localhost:5000/api/locations?accessible_by=bikes&lat=51.10&lon=17.05&limit=5'

.. code-block:: json

   [
     {
       "uuid": "7c3d5e7f-9a1b-4c3d-8e5f-7a9b1c3d5e7f",
       "position": [50.0397, 19.906],
       "remark": false
     }
   ]

``remark`` is a **boolean** — whether the point has a remark, not the remark itself.

Invalid or unknown query parameters are ignored rather than rejected.

``GET /api/locations-clustered``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The same filtered set, but with nearby points grouped server-side for the given zoom
level. This is what the frontend calls instead of ``/api/locations`` when
``USE_SERVER_SIDE_CLUSTERING`` is on.

Takes every parameter of :ref:`api-locations`, plus ``zoom`` (integer, **0–16**, default
``7``). A ``zoom`` outside that range is a ``400``.

.. code-block:: json

   [
     {
       "type": "cluster",
       "position": [50.1026, 19.8240],
       "uuid": null,
       "cluster_uuid": "34515392-7913-47be-a5b4-0c4b5247ad4c",
       "cluster_count": 2
     },
     {
       "type": "point",
       "position": [50.833, 15.917],
       "uuid": "9b1c3d5e-7f9a-4b1c-8d5e-9f1a3b5c7d9e",
       "cluster_uuid": null,
       "cluster_count": null
     }
   ]

Both kinds come back in one list, told apart by ``type``. A ``"point"`` carries a real
``uuid`` you can pass to :ref:`api-location-detail`; a ``"cluster"`` carries a
freshly-generated ``cluster_uuid`` (not stable across requests — it is a render key, not
an identifier) and the number of points it stands for. ``position`` is
``[latitude, longitude]``, as everywhere else.

.. _api-location-detail:

``GET /api/location/<uuid>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

One point, formatted for its popup.

.. code-block:: json

   {
     "title": "Zwierzyniecka",
     "subtitle": "small bridge",
     "position": [51.108056, 17.07],
     "data": [
       ["accessible_by", ["bikes", "pedestrians"]],
       ["is_free", "true"]
     ],
     "metadata": {
       "uuid": "c8ecf476-5968-40da-ba5c-e810ad9ff203"
     }
   }

``title`` is the point's ``name`` and ``subtitle`` its ``type_of_place``. ``data`` is a
list of ``[label, value]`` pairs — the fields listed in ``visible_data``, in that order,
with both label and value translated. ``metadata`` holds the ``meta_data`` fields. Fields
in neither list are not returned at all.

The path segment must be a valid UUID; anything else fails routing with ``404``. A
well-formed UUID that does not exist also gives ``404 {"message": "Location not found"}``.

``GET /api/categories-full``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every category with its options, defaults and filter mode — everything needed to render
the filter panel in one request.

.. code-block:: json

   {
     "categories": [
       {
         "key": "accessible_by",
         "name": "accessible_by",
         "options": [["bikes", "bikes"], ["cars", "cars"]],
         "default_checked": [],
         "filter_mode": "or"
       }
     ]
   }

``key`` is the query-parameter name to filter by; ``name`` is its translated label.
``options`` are ``[value, translated label]`` pairs — send the *value*.
``filter_mode`` tells you which control to draw: checkboxes for ``or``/``and``, radio
buttons for ``exclusive``/``threshold``, a single checkbox for ``boolean``
(:ref:`categories-filter-mode`).

With ``CATEGORIES_HELP`` on, each category also carries ``options_help``, and the response
gains a top-level ``categories_help`` — both lists of ``{option: help text}`` objects.

Prefer this endpoint over the two below, which exist for older clients and cost one
request per category.

``GET /api/categories``
~~~~~~~~~~~~~~~~~~~~~~~

Category names only, as ``[key, translated name]`` pairs. With ``CATEGORIES_HELP`` on,
returns ``{"categories": [...], "categories_help": [...]}`` instead — note the response
*type* changes with the flag.

``GET /api/category/<name>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The options for one category, as ``[value, translated label]`` pairs. With
``CATEGORIES_HELP`` on, returns
``{"categories_options": [...], "categories_options_help": [...]}``.

``GET /api/languages``
~~~~~~~~~~~~~~~~~~~~~~

The configured interface languages, exactly as given in ``LANGUAGES``:

.. code-block:: json

   {"en": {"name": "English", "flag": "gb", "country": "GB"}}

``GET /api/version``
~~~~~~~~~~~~~~~~~~~~

.. code-block:: json

   {"backend": "<installed-version>"}

The installed package version, normalised to PEP 440 — a release published as
``2.0.0-alpha.5`` reports as ``2.0.0a5``. Useful as a health check.

Submissions
-----------

Both endpoints below trigger whatever notifier plugin is active
(:ref:`data-source-plugins`), so a deployment with a mail notifier set up emails a
moderator on each submission.

``POST /api/suggest-new-point``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Submit a new point for review. It goes to the moderation queue with
``"status": "pending"`` — **it does not appear on the map**; someone has to move it into
the map data.

**The request must be ``multipart/form-data``.** The point goes in a single ``location``
form field as a JSON object — not as one form field per property — and the optional photo
goes in a ``photo`` file part. Send the point without a ``uuid``; the server assigns one:

.. code-block:: bash

   curl -X POST http://localhost:5000/api/suggest-new-point \
     -H "X-CSRFToken: $TOKEN" \
     -F 'location={"name": "Nowy", "position": [51.11, 17.03], "type_of_place": "small bridge", "accessible_by": ["bikes"], "is_free": "true"}' \
     -F 'photo=@bridge.jpg'

.. note::

   Sending the point as a JSON request body used to work and no longer does — a
   ``Content-Type: application/json`` request has no ``location`` form field, so it is
   rejected with ``400 {"message": "Invalid request data"}``. The same status comes back
   if ``location`` is missing, is not valid JSON, or is a JSON value that is not an
   object.

The submission is validated against ``location_obligatory_fields`` and ``categories``
(:doc:`data-source`). A missing obligatory field, or a value outside its category's
allowed list, gives ``400 {"message": "Invalid location data"}``. The response does not
say which field was wrong — that detail is logged server-side.

.. list-table::
   :header-rows: 1
   :widths: 12 88

   * - Status
     - Meaning
   * - ``200``
     - ``{"message": "Location suggested"}``
   * - ``400``
     - Invalid location data, a missing or malformed ``location`` field, a rejected photo,
       or a payload that is too deeply nested
   * - ``413``
     - The whole request body exceeded
       :ref:`the request size cap <api-request-size>`
   * - ``500``
     - Something failed while storing or notifying

**Photo uploads.** The ``photo`` part is optional; a suggestion without one is accepted.
The accepted formats and size limit come from the ``ATTACHMENT`` config key, which
defaults to **JPEG only, up to 5 MiB** (:ref:`config-attachment`). A photo that fails
either check is rejected with ``400`` and a message naming the allowed formats and limit,
e.g. ``Invalid photo. Allowed formats: jpeg, jpg. Max size: 5MiB.`` The photo is attached
to the notification, not stored as map data.

.. _api-request-size:

**Request size cap.** The app sets ``MAX_CONTENT_LENGTH`` to the configured attachment
limit plus 100 KB of headroom for the form fields and multipart framing. A body over that
is refused with ``413`` before it is read into memory. Raising ``ATTACHMENT.max_size``
raises this cap with it, so the two cannot drift apart.

.. note::

   The ``location`` field is parsed with hard limits to keep hostile input cheap to
   reject: at most 50 KB of JSON, nesting no deeper than arrays/objects of primitives,
   1000 characters per string, 100 array items, 50 object keys. Exceeding any of them
   gives ``400 {"message": "Invalid request: JSON payload too complex or too large"}``.
   Legitimate points are nowhere near these.

``POST /api/report-location``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Report a problem with an existing point.

.. code-block:: json

   {"id": "7c3d5e7f-9a1b-4c3d-8e5f-7a9b1c3d5e7f", "description": "has a hole"}

``description`` must be one of the ``reported_issue_types`` in your data source — unless
``"other"`` is among them, in which case any text up to 500 characters is accepted. A
description that satisfies neither rule gives ``400``.

The report is stored with ``"status": "pending"`` and ``"priority": "medium"`` in the
data source, for triage.

``GET /api/generate-csrf-token``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. deprecated:: 1.1.8

   Deprecated since 1.1.8 and kept only for backward compatibility. Read the token from
   the ``csrf-token`` meta tag instead. CSRF protection itself is unaffected.

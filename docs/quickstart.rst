Quickstart
==========

Configuration
-------------

Goodmap uses YAML configuration files. Create a configuration file (e.g., ``config.yml``):

.. code-block:: yaml

   APP_NAME: My awesome goodmap application
   SECRET_KEY: secret

   LANGUAGES:
     en:
       name: English
       flag: uk
       country: GB
     pl:
       name: polski
       flag: pl
       country: PL

   DB:
     TYPE: json_file
     PATH: data.json

   PLUGINS:
     sendmail:
       PORT: 465
       SERVER: "smtp.example.com"
       RECEIVER: "receiver@example.com"
       USER: "sender@example.pl"
       PASSWORD: "PA$$WORD"
       SUBJECT: "My awesome goodmap application"

Data Model
~~~~~~~~~~

Each location in the database has a set of fields (``name``, ``position``,
``type_of_place``, plus any custom fields defined by the application). Three
configuration keys control how these fields appear on the map:

``visible_data``
   List of field names to display **inline** in location markers (the popup
   that appears when a pin is clicked). Only fields listed here appear in the
   marker's data section; any other location fields are hidden from the
   frontend.

``meta_data``
   List of field names to display in the location detail panel (sidebar or
   modal), separate from the inline marker fields.

``location_obligatory_fields``
   List of ``(field_name, field_type)`` tuples that define **extra** fields
   (beyond the built-in ``name`` and ``position``) which are required when
   creating or editing a location. The frontend uses this to generate dynamic
   forms. Supported types: ``str``, ``list``, ``int``, ``float``, ``bool``,
   ``dict``.

Example configuration in your data source:

.. code-block:: json

   {
     "visible_data": ["test_category", "type_of_place"],
     "meta_data": ["uuid"],
     "location_obligatory_fields": [
       ["test_category", "list[str]"]
     ]
   }

.. _categories-filter-mode:

Categories and Filtering
~~~~~~~~~~~~~~~~~~~~~~~~

``categories`` is a dict of field name to the list of allowed values for that
field. Each category is rendered in the frontend as a group of filter
checkboxes, one per allowed value.

``categories_help``
   List of category keys that should show a help tooltip next to the
   category's title. The tooltip text is looked up via the translation key
   ``categories_help_<category_key>``.

``categories_options_help``
   Dict of category key to the list of option values within that category
   that should show a help tooltip. The tooltip text is looked up via the
   translation key ``categories_options_help_<option_value>``.

``categories_default_checked``
   Dict of category key to the list of option values that should be
   pre-checked in the filter panel when the app first loads, before the user
   has made any selection.

``categories_filter_mode``
   Dict of category key to how *multiple selected values within that
   category* are combined when filtering locations. Categories not listed
   here default to ``"or"``. This only affects combination **within** one
   category - across different categories, selections are always combined
   with AND (a location must match every category that has an active
   selection).

   ``"or"`` (default)
      A location matches if it has **any** of the selected values. This is
      the usual "check more boxes to broaden results" behavior - e.g.
      checking both ``bikes`` and ``cars`` on ``accessible_by`` shows
      locations that allow bikes *or* cars, not only locations that allow
      both (which would often be zero results).

   ``"and"``
      A location matches only if it has **every** one of the selected
      values - narrowing rather than broadening. Only meaningful for
      list-valued categories (a location can have several simultaneous
      values); for a single-valued category it behaves like ``"or"``
      restricted to one selection at a time. Still rendered as checkboxes
      (it's still multi-select), but with a "(match all)" hint next to the
      category title so it reads differently from the default "or"
      behavior - e.g. an ``amenities`` field where checking ``lighting``
      and ``benches`` should show only bridges that have both, not either.

   ``"exclusive"``
      Single-select: the frontend renders the options as radio buttons
      instead of checkboxes, so only one value can be active at a time. Use
      this for categories with three or more mutually-exclusive states,
      e.g. a toll tier: ``free`` / ``discounted`` / ``full_price``.

   ``"boolean"``
      For a field with exactly the two values ``"true"`` and ``"false"``.
      Only the ``"true"`` option is rendered, as a single checkbox; leaving
      it unchecked already means "show everything" (both true and false
      locations), so there's no separate control for isolating ``"false"``
      alone. Use this when nobody would deliberately filter for the
      negative case - e.g. a "free only" checkbox for an ``is_free`` field,
      since drivers care about "free" or "all", not "paid only".

   ``"threshold"``
      For an ordered, numeric-valued category, e.g. a speed limit in km/h.
      Selecting a value matches any location whose value is **at or below**
      the highest selected value - e.g. selecting ``30`` also matches
      locations with ``10`` or ``30``, but not ``50``. The frontend renders
      this as radio buttons too, since selecting more than one option would
      be redundant: the highest selection alone determines the cutoff.

Example configuration combining all five modes:

.. code-block:: json

   {
     "categories": {
       "accessible_by": ["bikes", "cars", "pedestrians"],
       "type_of_place": ["big bridge", "small bridge"],
       "is_free": ["true", "false"],
       "speed_limit": ["10", "30", "50"],
       "amenities": ["lighting", "benches", "toilets"]
     },
     "categories_help": ["accessible_by"],
     "categories_options_help": {
       "accessible_by": ["cars", "pedestrians"]
     },
     "categories_default_checked": {
       "accessible_by": ["cars"]
     },
     "categories_filter_mode": {
       "accessible_by": "or",
       "type_of_place": "or",
       "is_free": "boolean",
       "speed_limit": "threshold",
       "amenities": "and"
     }
   }

The active mode for each category is also exposed as ``filter_mode`` in the
``/api/categories-full`` response, so a custom frontend can render the
right control (checkbox vs. radio) without hardcoding category names.

Photo Uploads
~~~~~~~~~~~~~

Suggesting a new location (``POST /api/suggest-new-point``) accepts an
optional ``photo`` file alongside the location fields. The allowed formats
and maximum size come from platzky's own ``ATTACHMENT:`` config key (see
`platzky's AttachmentConfig
<https://platzky.readthedocs.io/en/latest/api.html#platzky.config.AttachmentConfig>`_),
which Goodmap defaults to JPEG-only, 5 MiB - a safe default for a field the
frontend always previews as an image and auto-compresses to JPEG when
oversized:

.. code-block:: yaml

   ATTACHMENT:
     allowed_mime_types: ["image/jpeg", "image/png"]
     allowed_extensions: ["jpg", "jpeg", "png"]
     max_size: 8388608  # 8 MiB

Omit ``ATTACHMENT:`` entirely to keep the JPEG-only 5 MiB default.

These constraints are exposed to the frontend as ``photo`` in the
``LOCATION_SCHEMA`` object rendered on the ``/map`` page
(``allowed_extensions``, ``allowed_mime_types``, ``max_size_bytes``), so a
custom frontend can read the live limits instead of hardcoding its own copy.

Client-side behavior
^^^^^^^^^^^^^^^^^^^^^

The bundled frontend checks format and size separately, and never changes a
photo without telling the user:

1. A photo that already matches the allowed mime type and size is used as-is,
   silently.
2. A photo with an unsupported mime type (e.g. PNG when only JPEG is allowed)
   is rejected outright, with an inline error naming the allowed formats.
   It is **not** auto-converted - silently swapping a user's PNG for a
   re-encoded JPEG behind their back would be surprising, so they have to
   explicitly pick a different file.
3. A photo with an allowed mime type that's simply too large is re-encoded as
   JPEG client-side: scaled down to fit 1920px on its longest side, then
   re-compressed at progressively lower quality (from 0.9 down to 0.4) until
   it fits under the size limit. This is announced up front, before
   compression starts (a large source photo can take a visible moment to
   decode and re-encode) - the upload button shows a spinner and is disabled
   while it runs, and the inline warning is updated once it finishes to
   confirm the photo was compressed and may have lost some quality.
4. If the recompressed photo is *still* too large, or the file can't be
   decoded as an image at all, the user sees a rejection instead.

Server-side validation
^^^^^^^^^^^^^^^^^^^^^^^

The backend independently validates the uploaded photo against the same
``photo_attachment_config`` regardless of what the client already checked -
a request with a disallowed mime type or a file over the size limit is
rejected with a 400 response, e.g.:

.. code-block:: json

   {"message": "Invalid photo. Allowed formats: jpeg, jpg. Max size: 5MiB."}

.. _data-model-visible_data:

Database Types
~~~~~~~~~~~~~~

JSON File:

.. code-block:: yaml

   DB:
     TYPE: json_file
     PATH: data.json

Google Cloud Storage:

.. code-block:: yaml

   DB:
     TYPE: google_hosted_json_file
     BUCKET_NAME: good-map
     SOURCE_BLOB_NAME: data.json

Running the Application
-----------------------

Development Server
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   poetry run flask --app "goodmap.goodmap:create_app(config_path='config.yml')" --debug run

The application will be available at http://localhost:5000

Building the Application
------------------------

To build translations and create a distribution:

.. code-block:: bash

   make build

This will compile translations and build the package.

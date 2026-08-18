Configuration
=============

Goodmap is configured by a single YAML file, whose path you pass to the application
factory:

.. code-block:: bash

   flask --app "goodmap.goodmap:create_app(config_path='config.yml')" run

The config controls **how the app runs**. What is *on* the map — the points, the
filterable fields, the popup contents — lives in the data source instead, documented in
:doc:`data-source`.

Because Goodmap is built on platzky, a Goodmap config *is* a platzky config plus the keys
Goodmap adds of its own — ``GOODMAP_FRONTEND_LIB_URL`` and ``ATTACHMENT``. Keys not listed
here are passed through to platzky; see
:doc:`platzky's configuration docs <platzky:index>` for the rest.

.. note::

   **Top-level** config keys are uppercase; nested ones are not, so ``ATTACHMENT`` is
   spelled in caps but its ``max_size`` is not. A missing config file exits with an error;
   an unreadable or invalid one raises at startup, so problems surface immediately rather
   than on first request.

.. warning::

   An unknown top-level key is **silently ignored**, not rejected — a typo in a key name
   costs you the setting with nothing in the log to say so. Check spelling against this
   page when a setting appears to have no effect.

A complete config
-----------------

Everything below in one file — copy it and delete what you do not need:

.. code-block:: yaml

   APP_NAME: My awesome goodmap application
   SECRET_KEY: replace-with-a-real-random-value

   LANGUAGES:
     en:
       name: English
       flag: gb
       country: GB
     pl:
       name: polski
       flag: pl
       country: PL

   DB:
     TYPE: json_file
     PATH: data.json

   ATTACHMENT:
     allowed_mime_types: ["image/jpeg"]
     allowed_extensions: ["jpg", "jpeg"]
     max_size: 5242880  # 5 MiB

   FEATURE_FLAGS:
     USE_LAZY_LOADING: true
     CATEGORIES_HELP: true
     SHOW_SEARCH_BAR: true
     SHOW_SUGGEST_NEW_POINT_BUTTON: true
     SHOW_ACCESSIBILITY_TABLE: true
     USE_SERVER_SIDE_CLUSTERING: false
     FAKE_LOGIN: false

   BLOG_PREFIX: "/blog"
   TRANSLATION_DIRECTORIES: ["/srv/myapp/translations"]

   GOODMAP_FRONTEND_LIB_URL: "/static/frontend/index.min.js"

The repository also ships ``config-template.yml`` as a starting point, and
``examples/e2e_test_config.yml`` as a config known to work with the bundled dataset.

Basic keys
----------

``APP_NAME``
   Site name, shown in the interface and page titles.

``SECRET_KEY``
   Flask's secret key: signs session cookies and CSRF tokens. **Must** be set to a real
   random value in production and kept out of version control — see
   :ref:`deployment-secrets`.

``LANGUAGES``
   The interface languages, as a mapping of language code to ``name``, ``flag``
   (a country code used to pick the flag icon), and ``country``. **The first entry is the
   default language.** Translations of your own category and field names go in
   ``TRANSLATION_DIRECTORIES``; see :ref:`config-translations`.

``BLOG_PREFIX``
   URL prefix for platzky's pages and blog, e.g. ``"/blog"``. The ``site_content.pages``
   entries in your data source are served under it.

``TRANSLATION_DIRECTORIES``
   Extra directories to load gettext catalogues from, on top of Goodmap's own. Use
   **absolute paths**: relative ones resolve against the installed platzky package, not
   your project.

.. _config-frontend-url:

``GOODMAP_FRONTEND_LIB_URL``
   Where the browser loads the frontend bundle from. Defaults to
   ``/static/frontend/index.min.js`` — the build shipped inside the package, served by
   Goodmap itself. Override it to:

   - serve the bundle from a CDN:
     ``"https://cdn.jsdelivr.net/npm/@problematy/goodmap@1.3.0"``
   - point at a local frontend dev server while working on the UI:
     ``"http://localhost:8080/index.min.js"``

   The URL is loaded with ``crossorigin="anonymous"``, so a remote host must send
   permissive CORS headers.

.. _config-db:

``DB``
   Which data source to read, and how to reach it. Every backend takes ``TYPE`` plus its
   own keys:

   .. code-block:: yaml

      DB:
        TYPE: json_file
        PATH: data.json

   .. code-block:: yaml

      DB:
        TYPE: google_json
        BUCKET_NAME: good-map
        SOURCE_BLOB_NAME: data.json

   The backends, their trade-offs, and the MongoDB layout are covered in
   :ref:`data-source-backends`.

.. _config-attachment:

``ATTACHMENT``
   What a visitor may attach as a photo when suggesting a new point. Omit it and you get
   **JPEG only, up to 5 MiB** — deliberately narrower than platzky's default, because the
   frontend previews the attachment as an ``<img>`` and compresses oversized ones to JPEG.

   .. code-block:: yaml

      ATTACHMENT:
        allowed_mime_types: ["image/jpeg", "image/png"]
        allowed_extensions: ["jpg", "jpeg", "png"]
        max_size: 8388608  # 8 MiB

   ``max_size`` is in bytes. Both the browser and the server enforce these limits, and the
   app's overall request-body cap is derived from ``max_size``
   (:ref:`the request size cap <api-request-size>`), so raising the limit here is the only
   change needed. A photo in an allowed format that is over the limit is compressed in the
   browser first, with a warning that quality may drop; if it is still too large it is
   rejected. An unsupported format is rejected outright.

.. _config-feature-flags:

Feature flags
-------------

``FEATURE_FLAGS`` is a flat mapping of flag name to boolean. Unset flags are off, with one
exception: ``USE_LAZY_LOADING`` defaults to on.

Flags fall into two groups: some change what the backend does, others are handed to the
frontend to decide what to render. Both are set the same way.

.. list-table::
   :header-rows: 1
   :widths: 30 12 58

   * - Flag
     - Acts on
     - Effect
   * - ``USE_LAZY_LOADING``
     - backend
     - **On by default.** Builds the location model from ``location_obligatory_fields``
       and ``categories`` in your data source, so submitted points are validated against
       them, and the "suggest a new point" form is generated from them. Set it to
       ``false`` and only ``uuid``, ``position`` and ``remark`` are validated, and the
       suggest form has no fields — see the note below.
   * - ``CATEGORIES_HELP``
     - both
     - Enables the help-tooltip data in ``/api/categories``, ``/api/categories-full`` and
       ``/api/category/<name>``, and makes the frontend render the tooltips. Without it
       the ``categories_help`` and ``categories_options_help`` keys in your data are
       ignored. See :ref:`data-source-help`.
   * - ``USE_SERVER_SIDE_CLUSTERING``
     - both
     - The frontend fetches ``/api/locations-clustered`` instead of ``/api/locations``,
       so nearby points are grouped into clusters by the server at the current zoom
       level. Worth it for large datasets; with it off, clustering happens in the
       browser.
   * - ``SHOW_SEARCH_BAR``
     - frontend
     - Shows the address search box (geocoding via OpenStreetMap Nominatim).
   * - ``SHOW_SUGGEST_NEW_POINT_BUTTON``
     - frontend
     - Shows the button that lets visitors submit a new point through
       ``/api/suggest-new-point``. Submissions land in the moderation queue, not on the
       map.
   * - ``SHOW_ACCESSIBILITY_TABLE``
     - frontend
     - Shows an alternative table view of the map data, for users who cannot use the map
       itself.
   * - ``FAKE_LOGIN``
     - backend
     - platzky flag: lets anyone log in by picking a role, with no authentication. For
       local development only.

.. warning::

   Never enable ``FAKE_LOGIN`` in production. It hands a logged-in session to anyone who
   asks for one.

.. note::

   ``USE_LAZY_LOADING`` is named for behaviour that is now unconditional: point details
   have their own endpoint (``/api/location/<uuid>``) whether the flag is set or not.
   What the flag still controls is schema validation, as described above. Leave it on
   unless you have a reason not to.

The frontend receives the whole ``FEATURE_FLAGS`` mapping, so a plugin or a custom build
can read flags Goodmap itself does not know about.

.. _config-plugins:

Plugins configuration
---------------------

**Plugins are not configured in config file.** Every plugin — Goodmap's map overlays and
marker-field renderers, and platzky's notifiers alike — is activated in the **data
source**, under its top-level ``plugins`` key:

.. code-block:: json

   {
     "plugins": {
       "some_plugin": { "is_active": true, "config": { } }
     }
   }

See :ref:`data-source-plugins` for the shape and :doc:`plugins` for writing one.

.. _config-translations:

Translating your own data
-------------------------

Category names, option values and field names are passed through gettext before being
returned by the API, so ``accessible_by`` and ``bikes`` can be displayed as real words in
each language. Goodmap ships catalogues for its own interface strings; strings that come
from *your* data are yours to translate:

1. Create a directory with the standard gettext layout::

      translations/
        en/LC_MESSAGES/messages.po
        pl/LC_MESSAGES/messages.po

2. Add a message for each category key, option value and visible field name.
3. Compile the catalogues (``pybabel compile -d translations``).
4. Point ``TRANSLATION_DIRECTORIES`` at the directory, using an absolute path.

Help tooltips use derived keys — ``categories_help_<category>`` and
``categories_options_help_<option>`` — see :ref:`data-source-help`.

Untranslated strings fall back to the key itself, so an incomplete catalogue degrades to
raw field names rather than breaking.

Deployment
==========

Going from ``flask run`` to something you can leave running.

Serving the app
---------------

``flask run`` is a development server — single-threaded and not built for load. Goodmap
depends on `gunicorn <https://gunicorn.org/>`_, so it is already installed:

.. code-block:: bash

   gunicorn "goodmap.goodmap:create_app(config_path='/srv/goodmap/config.yml')"

Bind address, worker count and logging are gunicorn's own options:

.. code-block:: bash

   gunicorn \
     --bind 0.0.0.0:8000 \
     --workers 4 \
     --access-logfile - \
     "goodmap.goodmap:create_app(config_path='/srv/goodmap/config.yml')"

Use an absolute config path: the app resolves ``DB.PATH`` relative to the working
directory, so a relative path breaks the moment something starts the process from
elsewhere.

Put a reverse proxy (nginx, Caddy, a cloud load balancer) in front for TLS.

.. _deployment-workers:

Workers and your backend
~~~~~~~~~~~~~~~~~~~~~~~~

How many workers you can run depends on the data source:

**MongoDB** — scale freely. The database arbitrates concurrent writes.

**json_file** — **run a single worker** if anything writes: new suggestions, new
reports. Each write rewrites the whole file. The rename is atomic, so the file is never
left half-written, but two processes that read-modify-write concurrently will lose one of
the two changes. A read-only map that takes no submissions is safe with any number of
workers.

**google_hosted_json_file** — read-only, so any number of workers is fine.

.. _deployment-secrets:

Secrets
-------

``SECRET_KEY`` signs session cookies and CSRF tokens. A guessable key means forgeable
sessions.

- Generate a real one: ``python -c "import secrets; print(secrets.token_hex(32))"``.
- Keep it out of version control. Since the config is YAML with no interpolation, either
  render the config at deploy time from your secret store, or keep a config file outside
  the repository readable only by the service user.

Rotating ``SECRET_KEY`` logs everyone out and invalidates outstanding CSRF tokens. That is
usually fine; do it deliberately.

Plugin credentials are the other half of this, and they are easy to miss: plugins are
configured in the **data source**, not in ``config.yml``
(:ref:`data-source-plugins`), so a mail notifier's SMTP password sits in the same
``data.json`` you may be tempted to commit alongside your points. A ``json_file`` data
source holding an active notifier is a secret-bearing file — keep it out of the repository
and readable only by the service user, the same as the config. This is one more reason to
prefer MongoDB or a bucket over a checked-in JSON file once a deployment is real.

Pre-flight checklist
--------------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Setting
     - For production
   * - ``SECRET_KEY``
     - A real random value, from outside the repository.
   * - ``FAKE_LOGIN``
     - **Off.** It bypasses authentication entirely.
   * - ``USE_WWW``
     - On only if you actually serve a ``www.`` hostname; it redirects every request.
   * - ``--debug`` / ``FLASK_DEBUG``
     - Off. It exposes tracebacks and an interactive console.
   * - ``GOODMAP_FRONTEND_LIB_URL``
     - Default (bundled) unless you deliberately serve the bundle elsewhere.
   * - ``DB.PATH``
     - Absolute, and writable by the service user if anything writes.

The frontend bundle
-------------------

By default the browser loads the bundle from ``/static/frontend/index.min.js``, served by
the app from inside the installed package. Nothing extra to deploy.

Two reasons to change ``GOODMAP_FRONTEND_LIB_URL``:

- **Serving from a CDN**, to take static traffic off the app. The script tag uses
  ``crossorigin="anonymous"``, so the host must send permissive CORS headers.
- **Running from a source checkout**, where the bundle is a gitignored build artifact —
  either run ``make build-frontend`` or point at a hosted build (see
  :doc:`installation`).

Data and backups
----------------

What you back up is the data source, and it is not static — accepted suggestions and
incoming reports change it while the app runs.

- **json_file** — back up the file itself. Because writes go through a temporary file and
  a rename, a copy taken at any moment is a consistent snapshot of some version. Note that
  this file also holds ``site_content``.
- **MongoDB** — your usual database backups; nothing Goodmap-specific.
- **google_hosted_json_file** — the blob is your source of truth and the app never writes
  to it. Bucket object versioning gives you history.

Schema keys (``categories``, ``visible_data``, ``location_obligatory_fields``) are read
at startup, so changing them means restarting the app. Point data is re-read per request.

Health checks
-------------

``GET /api/version`` is cheap and needs no data source, returning
``{"backend": "2.0.0a5"}``. Point your load balancer at it.

For a check that also proves the data source is reachable, use ``GET /api/locations`` —
it touches the backend, though on a large map it is not free.

Upgrading
---------

Goodmap 2.x is currently published as pre-releases, so pin an exact version and upgrade
deliberately:

.. code-block:: text

   goodmap==2.0.0a5

Before upgrading, read ``CHANGELOG.md`` in the repository. Note that 2.0 **requires every
point's ``uuid`` to be a real UUID** — arbitrary string ids are no longer routable and
give a ``404``. Migrate the data before upgrading, and validate it with the script in
:doc:`data-source`.

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

**json_file** — **run a single worker** if anything writes: accepted suggestions, new
reports, admin edits. Each write rewrites the whole file. The rename is atomic, so the
file is never left half-written, but two processes that read-modify-write concurrently
will lose one of the two changes. A read-only map (no admin panel, no submissions) is
safe with any number of workers.

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
- The same applies to notifier credentials under ``PLUGINS`` — an SMTP password in a
  committed ``config.yml`` is a leaked password.

Rotating ``SECRET_KEY`` logs everyone out and invalidates outstanding CSRF tokens. That is
usually fine; do it deliberately.

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
   * - ``ENABLE_ADMIN_PANEL``
     - Off unless you need it — and if you do, read :ref:`deployment-admin`.
   * - ``USE_WWW``
     - On only if you actually serve a ``www.`` hostname; it redirects every request.
   * - ``--debug`` / ``FLASK_DEBUG``
     - Off. It exposes tracebacks and an interactive console.
   * - ``GOODMAP_FRONTEND_LIB_URL``
     - Default (bundled) unless you deliberately serve the bundle elsewhere.
   * - ``DB.PATH``
     - Absolute, and writable by the service user if anything writes.

.. _deployment-admin:

Protecting the admin panel
--------------------------

``ENABLE_ADMIN_PANEL`` registers ``/api/admin/`` alongside the panel, and **those
endpoints do not authenticate the caller**. The HTML page checks for a session; the API
behind it does not. CSRF protection blocks a third-party site from driving a logged-in
browser, but it does nothing against a direct request — a client can fetch a token and
then call the API.

So on any reachable deployment with the panel on, add a layer of your own:

- Restrict ``/api/admin/`` and ``/goodmap-admin`` by source IP or VPN at the proxy.
- Or require proxy-level authentication (HTTP basic auth, mTLS, an SSO forward-auth) on
  those paths.
- Or leave ``ENABLE_ADMIN_PANEL`` off in the public deployment and moderate from a
  separate, restricted instance pointed at the same MongoDB.

An nginx sketch of the second option:

.. code-block:: nginx

   location ~ ^/(api/admin|goodmap-admin) {
       auth_basic           "Goodmap admin";
       auth_basic_user_file /etc/nginx/goodmap.htpasswd;
       proxy_pass           http://127.0.0.1:8000;
   }

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

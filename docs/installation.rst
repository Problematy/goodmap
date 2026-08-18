Installation
============

Requirements
------------

- **Python 3.10 or newer.**
- A data source — a local JSON file, a Google Cloud Storage bucket, or a MongoDB
  instance. A JSON file needs no external service, so you can start with nothing but a
  file on disk. See :doc:`data-source`.

Nothing else, if you install the published package: the React frontend and the compiled
interface translations ship inside it, so there is no frontend to host separately and no
Node.js involved.

A source checkout is different. Both the frontend bundle and the translation catalogs are
gitignored build output, so a clone additionally needs **Node.js and npm** to build them
— see `Installing from source`_.

Installing the package
----------------------

Goodmap is published on PyPI as `goodmap <https://pypi.org/project/goodmap/>`_:

.. code-block:: bash

   pip install goodmap

Or with Poetry, in the project that will host your map:

.. code-block:: bash

   poetry add goodmap

Checking it worked
------------------

Goodmap is a Flask application factory — ``goodmap.goodmap:create_app`` takes the path to
your YAML config and returns a configured app. With a ``config.yml`` in place (see
:doc:`quickstart`):

.. code-block:: bash

   flask --app "goodmap.goodmap:create_app(config_path='config.yml')" --debug run

Then ``curl http://localhost:5000/api/version`` should report the installed version:

.. code-block:: json

   {"backend": "<installed-version>"}

The value is the package version normalised to PEP 440, so a release published as
``2.0.0-alpha.5`` reports as ``2.0.0a5``.

Installing from source
----------------------

Install from a checkout if you want to run the bundled example, track an unreleased
change, or contribute (see :doc:`development`).

.. code-block:: bash

   git clone https://github.com/Problematy/goodmap.git
   cd goodmap
   poetry install

.. important::

   **This applies to source checkouts only.** ``pip install goodmap`` gives you the
   frontend already built — the wheel ships ``index.min.js`` — so an installed package
   needs no build step. A clone does: ``goodmap/static/frontend/`` is compiled output,
   gitignored and never committed, so a fresh checkout has nothing to serve.

   Nothing announces the problem: ``map.html`` pulls the bundle in with a plain
   ``<script src="/static/frontend/index.min.js">``, so the page still returns ``200``
   and the server logs stay quiet. What you see is a page with a blank space where the
   map belongs, and a ``404`` for ``index.min.js`` in the browser console.

   Build it once — this needs Node.js and npm:

   .. code-block:: bash

      make build-frontend

   That writes ``goodmap/static/frontend/index.min.js``, which the app picks up with no
   further configuration.

   To skip the build entirely, point the app at a hosted bundle instead by setting
   ``GOODMAP_FRONTEND_LIB_URL`` in your config (see :ref:`config-frontend-url`).

The repository is a monorepo: the Python backend at the root, the React frontend in
``frontend/``, and Playwright end-to-end tests in ``e2e-tests/``. Each has its own
dependency manager. Installing extras and dev tooling:

.. code-block:: bash

   poetry install --with dev       # pytest, black, ruff, pyright, coverage
   poetry install --extras docs    # sphinx, to build these docs

Running the bundled example
---------------------------

The repository ships a working config and dataset (bridges in Wrocław) under
``examples/``. From a source checkout, with the frontend built:

.. code-block:: bash

   make run-example-env

That is a shortcut for:

.. code-block:: bash

   poetry run flask --app "goodmap.goodmap:create_app(config_path='examples/e2e_test_config.yml')" --debug run

Open http://localhost:5000/ and you get a map with two bridges, category filters, and a
working popup. It is the fastest way to see what the pieces in :doc:`configuration` and
:doc:`data-source` actually do.

.. note::

   ``examples/e2e_test_config.yml`` sets ``GOODMAP_FRONTEND_LIB_URL`` to a CDN build, so
   it renders even without running ``make build-frontend``.

Next steps
----------

- :doc:`quickstart` — build your own map from an empty directory.
- :doc:`configuration` — every key you can put in ``config.yml``.

Installation
============

Requirements
------------

- **Python 3.10 or newer.**
- A data source: nothing (a local JSON file is fine), a Google Cloud Storage bucket, or
  a MongoDB instance. See :doc:`data-source`.

Nothing else. The React frontend and the interface translations are compiled into the
published package, so there is no separate Node.js build step and no separate frontend
to host.

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

   git clone --recursive https://github.com/Problematy/goodmap.git
   cd goodmap
   poetry install

.. important::

   A source checkout has **no frontend bundle** — it is a build artifact and is
   gitignored. Until you build it, the map page loads with no map. Either build it once:

   .. code-block:: bash

      make build-frontend      # requires Node.js/npm; writes goodmap/static/frontend/index.min.js

   or point the app at a hosted build instead, by setting ``GOODMAP_FRONTEND_LIB_URL`` in
   your config (see :ref:`config-frontend-url`).

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

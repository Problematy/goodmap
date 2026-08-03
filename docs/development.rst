Contributing
============

This page is about working on the Goodmap repository itself. If you are running or
extending an instance, the rest of the docs covers that.

See ``CONTRIBUTING.md`` in the repository for the process side — issue assignment,
priorities, and what a PR must satisfy to be merged.

The repository
--------------

Goodmap is a monorepo with three sub-projects, each with its own dependency manager and
Makefile:

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Directory
     - Manager
     - What it is
   * - repo root
     - poetry
     - The Python backend, built on platzky and published to PyPI as ``goodmap``.
   * - ``frontend/``
     - npm
     - The React frontend. Bundled into the PyPI package, not published separately.
   * - ``e2e-tests/``
     - poetry
     - Playwright end-to-end tests exercising backend and frontend together.

The root ``Makefile`` has targets that span all three — anything named ``*-all``.

Setting up
----------

.. code-block:: bash

   git clone --recursive https://github.com/Problematy/goodmap.git
   cd goodmap
   poetry install --with dev

Then, for whichever parts you are touching:

.. code-block:: bash

   make -C frontend install         # frontend work
   cd e2e-tests && poetry install   # e2e work

Python 3.10 is the supported floor. If your system Python differs, install 3.10 alongside
with `pyenv <https://github.com/pyenv/pyenv>`_.

The one-shot loop
-----------------

.. code-block:: bash

   make dev

Runs ``lint-fix-all``, then ``lint-check-all`` (including type-checking), then the backend
unit tests. This is the command to run before pushing.

Narrower variants:

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Target
     - Does
   * - ``make lint-fix``
     - black + ruff ``--fix`` on the backend
   * - ``make lint-check``
     - black, ruff, pyright and interrogate on the backend, changing nothing
   * - ``make lint-check-all``
     - the above plus the frontend and e2e-tests linters
   * - ``make check``
     - lint + all unit tests, backend and frontend, without modifying files
   * - ``make test-all``
     - backend and frontend unit tests

Code style is enforced, not negotiated: black and ruff at a 100-character line length,
pyright in strict mode, and interrogate requiring 95% docstring coverage on the backend.

Tests
-----

**Backend unit tests** (``tests/``, pytest):

.. code-block:: bash

   make unit-tests
   make coverage        # branch coverage, lcov output
   make html-cov        # browsable HTML report

Coverage must not drop — the suite fails under 95%. Tests marked ``skip_coverage`` are
excluded from the coverage run and have their own target,
``make unit-tests-no-coverage``.

**Frontend unit tests**:

.. code-block:: bash

   make -C frontend unit-tests

**End-to-end tests** need both servers running, in three terminals:

.. code-block:: bash

   make run-e2e-backend    # generates config + fresh test data, serves backend on :5000
   make run-frontend       # frontend on :8080
   make e2e-tests          # checks both are up, then runs Playwright

``run-e2e-backend`` regenerates the templated config and a fresh copy of the test data
each time, so a run never inherits state from the last one. ``make e2e-tests`` checks both
servers once and exits with a message naming the missing one rather than failing
obscurely.

Stress tests use a large generated dataset:

.. code-block:: bash

   make -C e2e-tests e2e-stress-tests-generate-data   # once; the dataset is large
   make run-e2e-stress-backend
   make run-frontend
   make e2e-stress-tests

A new feature is expected to come with e2e coverage.

Building
--------

.. code-block:: bash

   make build-frontend   # webpack build into goodmap/static/frontend/
   make build            # compiles translations, builds the frontend, builds the wheel

The frontend bundle is gitignored and produced by the build, but it *is* shipped in both
the sdist and the wheel — a checkout has no bundle until you build one, which is why a
freshly cloned repo serves a map-less page until ``make build-frontend`` runs.

Translations
------------

Interface strings live in ``goodmap/locale/``. After adding or changing a
``gettext``/``lazy_gettext`` call:

.. code-block:: bash

   make extract-translations

That extracts messages into ``extracted.pot`` and merges them into the per-language
``.po`` files without clobbering existing translations. Fill in the new entries, then
``make build`` compiles them.

Strings coming from a deployment's *data* — category names, option values — are not
extracted; those are the deployer's to translate (:ref:`config-translations`).

Dependencies
------------

.. code-block:: bash

   make dependency-check       # pip-audit on the backend
   make dependency-check-all   # backend, frontend, and e2e-tests

The ``-all`` variant approximates the dependency review CI runs on pull requests, so it
catches a vulnerable transitive dependency before the PR does.

Building these docs
-------------------

.. code-block:: bash

   poetry install --extras docs
   make -C docs html

Output lands in ``docs/_build/html/``. ``make -C docs help`` lists the other builders.

The docs are reStructuredText built with Sphinx, published on Read the Docs from
``.readthedocs.yaml``. They are intentionally **task-oriented**: they document how to use
Goodmap, not what its functions look like. There is no autodoc API dump — behaviour that
matters to a user of the project belongs in prose on the relevant page, and the running
app already serves its own OpenAPI schema at ``/api/doc`` for exact request and response
shapes.

When you change behaviour, update the page that describes it:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Change
     - Page
   * - A config key or feature flag
     - :doc:`configuration`
   * - The data format or a filter mode
     - :doc:`data-source`
   * - An endpoint's behaviour
     - :doc:`http-api`
   * - A plugin capability or its contract
     - :doc:`plugins`

Cross-page links use ``:doc:`` and ``:ref:``, so a moved section is caught as a build
warning rather than becoming a dead link.

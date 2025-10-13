Development
===========

Setting Up Development Environment
-----------------------------------

1. Install dependencies including development tools:

   .. code-block:: bash

      poetry install --with dev

2. Run linting and type checking:

   .. code-block:: bash

      make lint-check

3. Fix linting issues automatically:

   .. code-block:: bash

      make lint-fix

Running Tests
-------------

Unit Tests
~~~~~~~~~~

Run all unit tests:

.. code-block:: bash

   make unit-tests

Run unit tests without coverage markers:

.. code-block:: bash

   make unit-tests-no-coverage

E2E Tests
~~~~~~~~~

Run end-to-end tests:

.. code-block:: bash

   make e2e-tests

Run stress tests:

.. code-block:: bash

   make e2e-stress-tests-generate-data
   make e2e-stress-tests

Coverage
~~~~~~~~

Generate coverage reports:

.. code-block:: bash

   make coverage

Generate HTML coverage report:

.. code-block:: bash

   make html-cov

Code Quality
------------

The project uses:

- **black** - Code formatting
- **ruff** - Linting
- **pyright** - Type checking

All checks are run with:

.. code-block:: bash

   make lint-check

Internationalization
--------------------

Extract translation strings:

.. code-block:: bash

   make extract-translations

Translations are stored in ``goodmap/locale/`` directory.

Data Validation
---------------

Validate JSON data files:

.. code-block:: bash

   make verify-json-data JSON_DATA_FILE=path/to/data.json

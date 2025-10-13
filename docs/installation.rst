Installation
============

Requirements
------------

- Python 3.10 or higher
- Poetry (for dependency management)

Installing with Poetry
----------------------

.. code-block:: bash

   git clone https://github.com/Problematy/goodmap.git
   cd goodmap
   poetry install

This will install all required dependencies.

Installing Documentation Dependencies
--------------------------------------

To build the documentation locally:

.. code-block:: bash

   poetry install --extras docs

Development Dependencies
------------------------

To install development dependencies (for testing and linting):

.. code-block:: bash

   poetry install --with dev

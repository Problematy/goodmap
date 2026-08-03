Goodmap Documentation
=====================

Goodmap is a map engine: you give it a **data source** (a JSON file, a JSON blob in
Google Cloud Storage, or MongoDB) describing points on a map, plus a **YAML config
file**, and you get a running web application with a filterable map, marker popups,
a "suggest a new point" flow, an issue-reporting flow, an admin panel, and a JSON
HTTP API.

Goodmap is built on `platzky <https://platzky.readthedocs.io/>`_, so a Goodmap
deployment is also a platzky site (pages, menus, translations, plugins) with the map
mounted on top of it. The React frontend ships inside the ``goodmap`` package — you do
not need to build or host it separately.

These docs are task-oriented and split three ways:

**Running a Goodmap**
   You want an instance of your own. Install it, write ``config.yml``, author the data,
   moderate what users submit, put it in production. No Python required.

**Extending Goodmap**
   You are building against an instance — calling the HTTP API from your own client, or
   writing a plugin that adds behaviour to the map.

**Contributing**
   You are working on the Goodmap repository itself.

.. toctree::
   :maxdepth: 2
   :caption: Running a Goodmap

   installation
   quickstart
   configuration
   data-source
   admin-panel
   deployment

.. toctree::
   :maxdepth: 2
   :caption: Extending Goodmap

   http-api
   plugins

.. toctree::
   :maxdepth: 2
   :caption: Contributing

   development

Where things live
-----------------

A Goodmap deployment has exactly two things you author:

``config.yml``
   How the app runs: name, languages, which data source to read, which feature flags
   are on. See :doc:`configuration`.

the data source
   What is on the map: the points themselves, which fields are shown, which fields are
   filterable, which plugins are active. See :doc:`data-source`.

Everything else — the map UI, the HTTP API, the admin panel — comes from the package.

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

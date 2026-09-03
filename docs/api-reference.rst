Python API reference
====================

Generated from the source. This is the reference for code you *import* — writing a
plugin, embedding the app, or working on Goodmap itself. If you are calling Goodmap over
HTTP instead, you want :doc:`http-api`; if you are configuring an instance, you want
:doc:`configuration`.

Nothing here is a substitute for the task pages: use those to find out *which* thing to
reach for, and this page for its exact signature.

.. note::

   Only the ``goodmap`` package is covered. Everything a Goodmap deployment inherits from
   platzky — the engine, blog, plugin loader — is documented in
   :doc:`platzky's own reference <platzky:index>`.

Creating the application
------------------------

The documented way to build an app is the factory, given a path to ``config.yml``. It is
what ``flask --app`` and ``gunicorn`` take as their target string (:doc:`deployment`).

.. autofunction:: goodmap.goodmap.create_app

.. autoclass:: goodmap.config.GoodmapConfig
   :members:
   :show-inheritance:

``GoodmapConfig`` is a platzky ``Config`` with Goodmap's extra keys, and it is what
``create_app`` parses the YAML into. The prose description of every key is in
:doc:`configuration`.

Plugins
-------

The capability base classes a plugin subclasses. Which capability does what, and how a
plugin is packaged and activated, is covered in :doc:`plugins`.

.. automodule:: goodmap.plugin
   :members:
   :show-inheritance:

Location data
-------------

The models every point is validated against — both points already in the data source and
points arriving through ``/api/suggest-new-point``. ``create_location_model`` is the one
to know: it builds a model from your data source's ``location_obligatory_fields`` and
``categories`` at startup, which is why those keys are validation rules and not just
documentation (:doc:`data-source`).

.. automodule:: goodmap.data_models.location
   :members:
   :show-inheritance:

Request and response models
---------------------------

Pydantic models for the HTTP layer. These are what generate the OpenAPI document served
at ``/api/doc/openapi.json``, so they and the schema endpoint never disagree.

.. automodule:: goodmap.api.api_models
   :members:
   :show-inheritance:

Data access
-----------

The data-source layer: one implementation per ``DB.TYPE``, plus the query functions the
API blueprint calls. Backend trade-offs and the MongoDB layout are in
:ref:`data-source-backends`.

.. automodule:: goodmap.db
   :members:
   :show-inheritance:

Querying, filtering and clustering
----------------------------------

How a request's query parameters become a list of points: filter combination, distance
sorting and limiting, then optional server-side clustering.

.. automodule:: goodmap.core
   :members:

.. automodule:: goodmap.filtering
   :members:

.. automodule:: goodmap.clustering
   :members:

Formatting
----------

Translation of category keys, option values and field names on the way out
(:ref:`config-translations`).

.. automodule:: goodmap.formatter
   :members:

Marker presentation
-------------------

What a point looks like before the browser gets it: the built-in field types goodmap renders
itself, the pin icon/color lookup tables, and the view the map opens on
(:ref:`data-source-initial_view`, :ref:`data-source-marker-styles`).

.. automodule:: goodmap.field_types
   :members:
   :show-inheritance:

.. automodule:: goodmap.marker_styles
   :members:

.. automodule:: goodmap.initial_view
   :members:
   :show-inheritance:

Errors
------

Exceptions raised by the data layer, and the helpers that turn them into the deliberately
generic ``{"message": "..."}`` responses described in :doc:`http-api`.

.. automodule:: goodmap.exceptions
   :members:
   :show-inheritance:

Input hardening
---------------

Limits applied to JSON arriving from the network before it is parsed into a point. The
concrete numbers, and the response you get for exceeding them, are in
:doc:`http-api`.

.. automodule:: goodmap.json_security
   :members:
   :show-inheritance:

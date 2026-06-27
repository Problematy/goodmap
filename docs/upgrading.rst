Upgrading
=========

This page records breaking changes that require action when upgrading an
existing deployment.

Aligning with platzky 2.0 breaking changes
------------------------------------------

This release tracks breaking changes in ``platzky`` and changes two things
existing deployments must account for.

Map view moved from ``/`` to ``/map``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``platzky`` now owns the root path and dispatches it through the site's home
page. The map view is registered at ``/map``. To keep ``/`` rendering the map,
set ``site_content.home_page_path`` to ``"/map"`` in your database content:

.. code-block:: json

   {
     "site_content": {
       "home_page_path": "/map"
     }
   }

Without this, visiting ``/`` no longer serves the map.

Frontend bundle is served locally by default
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``GOODMAP_FRONTEND_LIB_URL`` no longer defaults to a CDN URL. When it is unset,
the backend serves the ``index.min.js`` bundle shipped inside the PyPI package
from ``/static/frontend/index.min.js``. Set ``GOODMAP_FRONTEND_LIB_URL`` only
when you want to override the bundle with an external URL (for example, a CDN
or a separately hosted build).

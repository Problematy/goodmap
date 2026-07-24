Quickstart
==========

Configuration
-------------

Goodmap uses YAML configuration files. Create a configuration file (e.g., ``config.yml``):

.. code-block:: yaml

   APP_NAME: My awesome goodmap application
   SECRET_KEY: secret

   LANGUAGES:
     en:
       name: English
       flag: uk
       country: GB
     pl:
       name: polski
       flag: pl
       country: PL

   DB:
     TYPE: json_file
     PATH: data.json

   PLUGINS:
     sendmail:
       PORT: 465
       SERVER: "smtp.example.com"
       RECEIVER: "receiver@example.com"
       USER: "sender@example.pl"
       PASSWORD: "PA$$WORD"
       SUBJECT: "My awesome goodmap application"

Data Model
~~~~~~~~~~

Each location in the database has a set of fields (``name``, ``position``,
``type_of_place``, plus any custom fields defined by the application). Three
configuration keys control how these fields appear on the map:

``visible_data``
   List of field names to display **inline** in location markers (the popup
   that appears when a pin is clicked). Only fields listed here appear in the
   marker's data section; any other location fields are hidden from the
   frontend.

``meta_data``
   List of field names to display in the location detail panel (sidebar or
   modal), separate from the inline marker fields.

``location_obligatory_fields``
   List of ``(field_name, field_type)`` tuples that define **extra** fields
   (beyond the built-in ``name`` and ``position``) which are required when
   creating or editing a location. The frontend uses this to generate dynamic
   forms. Supported types: ``str``, ``list``, ``int``, ``float``, ``bool``,
   ``dict``.

Example configuration in your data source:

.. code-block:: json

   {
     "visible_data": ["test_category", "type_of_place"],
     "meta_data": ["uuid"],
     "location_obligatory_fields": [
       ["test_category", "list[str]"]
     ]
   }

Categories and Filtering
~~~~~~~~~~~~~~~~~~~~~~~~

``categories`` is a dict of field name to the list of allowed values for that
field. Each category is rendered in the frontend as a group of filter
checkboxes, one per allowed value.

``categories_help``
   List of category keys that should show a help tooltip next to the
   category's title. The tooltip text is looked up via the translation key
   ``categories_help_<category_key>``.

``categories_options_help``
   Dict of category key to the list of option values within that category
   that should show a help tooltip. The tooltip text is looked up via the
   translation key ``categories_options_help_<option_value>``.

``categories_default_checked``
   Dict of category key to the list of option values that should be
   pre-checked in the filter panel when the app first loads, before the user
   has made any selection.

Example configuration in your data source:

.. code-block:: json

   {
     "categories": {
       "accessible_by": ["bikes", "cars", "pedestrians"],
       "type_of_place": ["big bridge", "small bridge"]
     },
     "categories_help": ["accessible_by"],
     "categories_options_help": {
       "accessible_by": ["cars", "pedestrians"]
     },
     "categories_default_checked": {
       "accessible_by": ["cars"]
     }
   }

.. _data-model-visible_data:

Database Types
~~~~~~~~~~~~~~

JSON File:

.. code-block:: yaml

   DB:
     TYPE: json_file
     PATH: data.json

Google Cloud Storage:

.. code-block:: yaml

   DB:
     TYPE: google_hosted_json_file
     BUCKET_NAME: good-map
     SOURCE_BLOB_NAME: data.json

Running the Application
-----------------------

Development Server
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   poetry run flask --app "goodmap.goodmap:create_app(config_path='config.yml')" --debug run

The application will be available at http://localhost:5000

Building the Application
------------------------

To build translations and create a distribution:

.. code-block:: bash

   make build

This will compile translations and build the package.

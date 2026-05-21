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

``data_templates``
   Per-value defaults keyed by a field name and its possible values. When a
   point has a matching field value, the corresponding template fields are
   merged in. Point-level fields always win.

   This lets you define "presets" for recurring location types so shared
   fields don't have to be repeated on every record.

   .. code-block:: json

      {
        "data_templates": {
          "type_of_place": {
            "big bridge": {
              "accessible_by": ["pedestrians", "cars"],
              "material": "steel"
            },
            "small bridge": {
              "accessible_by": ["pedestrians"],
              "material": "concrete"
            }
          }
        }
      }

   With this configuration a point that only stores ``{"type_of_place": "big bridge"}``
   will automatically receive ``accessible_by`` and ``material`` without those
   fields being duplicated in every record.

Example configuration in your data source:

.. code-block:: json

   {
     "visible_data": ["test_category", "type_of_place"],
     "meta_data": ["uuid"],
     "location_obligatory_fields": [
       ["test_category", "list[str]"]
     ],
     "data_templates": {
       "type_of_place": {
         "big bridge": {"accessible_by": ["pedestrians", "cars"]},
         "small bridge": {"accessible_by": ["pedestrians"]}
       }
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

![Github Actions](https://github.com/problematy/goodmap/actions/workflows/tests.yml/badge.svg?event=push&branch=main)
[![Coverage Status](https://coveralls.io/repos/github/Problematy/goodmap/badge.png)](https://coveralls.io/github/Problematy/goodmap)

# Good Map

Map engine to serve all the people ;) 

## Setup

#### 1. Use python 3.10
If you have a different version of Python on your system, install python 3.10 alongside. For that, you can use [`pyenv`](https://github.com/pyenv/pyenv). Follow the [documentation](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation). Useful commands: `pyenv help <command>`, `pyenv install`, `pyenv shell`, `pyenv versions`.

#### 2. Install `poetry` in Python 3.10
`poetry` can create virtual environments associated with a project. \
Make sure you are in the Python 3.10 environment and install:
```
pip install poetry
```
Useful commands: `poetry -h <command>`, `poetry env list`, `poetry env info`.

#### 3. Install dependencies
```
poetry install
```

#### 4. You're ready

When you enter the project directory, you can invoke any commands in your project like this:
```
poetry run <command>
```

## Running App locally

### TL;DR
If you don't want to go through all the configuration, e.g. you just simply want to test if everything works,
you can simply run app with test dataset provided in `tests/e2e_tests` directory:

> poetry run flask --app 'goodmap.goodmap:create_app(config_path="./tests/e2e_tests/e2e_test_config.yml")' run

### Configuration

If you want to serve app with your configuration rename config-template.yml to config.yml and change its contents according to your needs.
Values descriptions you can find inside config-template.yml.

Afterwards run it with:
> poetry run flask --app 'goodmap.goodmap:create_app(config_path="/PATH/TO/YOUR/CONFIG")' --debug run

## Database

The database is stored in a JSON file in the `map` section. The first subsection `data` consists of the actual datapoints, representing points on a map.

Datapoints have fields. The schema of these fields in defined in the rest of the subsections:
- `obligatory-filterable` - fields that are required for every datapoint and by which datapoints can be filtered in the app. These fields will have specified domains and every datapoint must have these fields set to one of the values from the domain. E.g.
```
  "type_of_place": [
    "big bridge",
    "small bridge"
]
```
- `obligatory` - the rest of the fields that are required for every datapoint. E.g.
```
"position",
"name"
```
- `visible_data` - when a datapoint will be rendered as a pin on a map, these are the fields that will be shown in the box when clicking on a pin. E.g.
```
"type_of_place"
```
- `meta-data` - ??

You can define the fields in all these sections, keeping in mind the assumptions about them specified above. The app relies on these assumptions.
Besides these types of fields, there is no restriction on the number of fields a datapoint can have.

## Examples

You can find examples of working configuration and database in `tests/e2e_tests` named:
- `e2e_test_config.yml`
- `e2e_test_data.json`

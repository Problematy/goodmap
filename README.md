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

The database is stored in JSON, in the `map` section. For an example database see `tests/e2e_tests/e2e_test_data.json`. The first subsection `data` consists of the actual datapoints, representing points on a map.

Datapoints have fields. The next subsections define special types of fields:
- `obligatory_fields` - here are explicitely stated all the fields that the application assumes are presnt in all datapoints. E.g.
```
"position",
"name",
"accessible_by"
```
TODO: `obligatory_fields` is a new subsection, start using it in the actual application
- `categories` - fields that can somehow be used in the app, for example by which datapoints can be filtered. Every category has a specified list of allowed values. E.g.
```
"accessible_by": ["bikes", "cars", "pedestrians"]
```
- `visible_data` - when a datapoint will be rendered as a pin on a map, these fields will be shown in the box when clicking on a pin. E.g.
```
"name",
"type_of_place"
```
- `meta-data` - some special data like 
```
"UUID"
```

You can define the fields in all these subsections. Besides these types of fields, there is no restriction on the number of fields a datapoint can have.

## Examples

You can find examples of working configuration and database in `tests/e2e_tests` named:
- `e2e_test_config.yml`
- `e2e_test_data.json`

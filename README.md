![Github Actions](https://github.com/problematy/goodmap/actions/workflows/tests.yml/badge.svg?event=push&branch=main)
[![Coverage Status](https://coveralls.io/repos/github/Problematy/goodmap/badge.png)](https://coveralls.io/github/Problematy/goodmap)

# Good Map

Map engine to serve all the people ;) 

## Setup

#### 1. Use python 3.10.
If you have a different version of Python on your system, install python 3.10 alongside. \
If you can't or don't know how to install another version of python on your system, you can use [`pyenv`](https://github.com/pyenv/pyenv). In this case follow these steps, refering to to `pyenv` [documentation](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation) for details:
- Install and set up `pyenv` (get the package and modify rc file of your shell)
- Using `pyenv` install Python version 3.10
```
pyenv install 3.10
```
- You can enter the pyenv environemnt by
```
pyenv shell 3.10
```
To view installed versions of python in pyenv, run `pyenv versions`.
You can always test which python version is currently used in your shell session by running `python --version` or `which python`.

#### 2. Set up `poetry` virtualenv.
`poetry` can create virtualenvs associated with a project
- Install `poetry`. **Note:** you need to install it based on Python 3.10. If you use `pyenv` make sure you are in the pyenv environment as shown above.

```
pip install poetry
```
- Create `poetry` virtual env
```
poetry env use
```
To view poetry virtualenvs associated with the current project, run `poetry env list`. \
To view information on the currrent virtualenv, run `poetry env info`.

#### 3. Install dependencies
```
poetry install
```

Now you have a ready environment. If everything worked fine, from now on you don't have to invoke `pyenv` at all. Any time you enter the project directory, `poetry` will automatically detect the virtualenv it created. Then you can invoke any commands in your project like this:
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

Database consists of three sections:

- `categories` - which informs on what categories data of points is divided
- `visible_data` - list of categories which will be visible by application users
- `data` - actual data split into `categories`


### `categories`
Fully configurable map where key is name of category and value is list of allowed types. E.g.
* "car_elements": ["mirror", "wheel", "steering wheel"]
* "color": ["red", "blue", "green"]

### `data`
Data consists of two parts:
* obligatory and constant
  * `name` - name of the object
  * `position` - coordinates of object
* category dependent - depending on your `categories` setup it varies. See example of config below.

#### `custom data`
You can define your own, more complex data types as dictionary.
* obligatory fields in dictionary:
  * `type` - type of data
  * `value` - value of data
* optional fields in dictionary:
  * `displayValue` - value to display instead of `value`

## Examples

You can find examples of working configuration and database in `tests/e2e_tests` named:
- `e2e_test_config.yml`
- `e2e_test_data.json`

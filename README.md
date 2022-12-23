![Github Actions](https://github.com/problematy/goodmap/actions/workflows/tests.yml/badge.svg?event=push&branch=main)
[![Coverage Status](https://coveralls.io/repos/github/Problematy/goodmap/badge.png)](https://coveralls.io/github/Problematy/goodmap)

# Good Map

Map engine to serve all the people ;) 

## Setup

### System dependencies
To run goodmap instance you'll need to install those dependencies:
- python 3.10
- poetry 1.20

### Project dependencies
We use `poetry` to serve project dependencies. To install all needed python dependencies:
* go to project directory
* use `poetry install`

## Running App locally

### TL;DR
If you don't want to go through all the configuration, e.g. you just simply want to test if everything works,
you can simply run app with test dataset provided in `tests/e2e_tests` directory:

> poetry run flask --app 'goodmap.goodmap:create_app(config_path="./tests/e2e_tests/e2e_test_config.yml")' run

### Configuration

If you want to serve app with your configuration rename config-template.yml to config.yml and change its contents according to your needs.
Values descriptions you can find inside config-template.yml.

Afterwards run it with:
> poetry run flask --app 'goodmap.goodmap' --debug run

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

## Examples
You can find examples of working configuration and database in `tests/e2e_tests` named:
- `e2e_test_config.yml`
- `e2e_test_data.json`

# Version History

### 0.1 - Initial Release - in development
#### 0.1.5 - in development
  * better looking frontend

#### 0.1.4 - Makeover
  * frontend for mobile version

#### 0.1.3 - Simplification
  * Simplified and standarized configuration in code
  * Extracted project dependencies to other repositoriesq
  * Updated dependencies

#### 0.1.1 - Static frontend
  * Using frontend served in npm  

#### 0.1.0 - First working version
 * JSON and Google hosted JSON database
 * Map displays points from database

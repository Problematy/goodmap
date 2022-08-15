![Github Actions](https://github.com/raven-wing/goodmap/actions/workflows/python-app.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/Problematy/goodmap/badge.png)](https://coveralls.io/github/Problematy/goodmap)

# GoodMap

Simple POI map overlay engine, for any of your custom data.

## Supported environment:

* `Python` (3.10),
* `Poetry` (1.1.13),
* `nodejs` (12.22.9),
* `npm` (8.3.1).

(Other versions not tested.)

## Running App locally

### Application

Local testing of the application requires a little different set of operations to execute, than what happens during production deployment (on Google Cloud Platform). To run the stack, execute in the same order:

1. rename `config-template.yml` to `config.yml` and change it's contents according to your needs (values descriptions you can find inside `config-template.yml`),
2. go to frontend directory,
3. install all dependencies with `npm install`,
4. build app by creating static file `npm run build`,
5. go to project directory,
6. use `poetry install`,
7. get into poetry shell `poetry shell`,
8. run `FLASK_ENV=development;FLASK_APP=goodmap.goodmap flask run`.

### Frontend

If you want to run only fronted:

* go to frontend directory,
* install all dependencies with `npm install`,
* `npm run build` -- if you want to build app by creating static file (as in production envarioment),
* `npm run serve` -- if you want to run javasript server locally,
* set `development_overwrites` for wanted endpoints, otherwise application will use compiled files.

### Backend

If you want to run only backend:
All dependencies are specified in `__pyproject.toml__` file. To install them in your onw environment:

* go to project directory,
* `poetry install` -- run this to install project dependencies,
* `poetry shell` -- enter Poetry shell, so you can start local backend app,
* (bash users) `FLASK_ENV=development;FLASK_APP=goodmap.goodmap flask run` -- this will run the app with development environment pushed as environment variables.

## Database

Database consists of three sections:

- `categories` - which informs on what categories data of points is divided
- `visible_data` - list of categories which will be visible by application users
- `data` - actual data splitted into `categories`


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

### Config example
```
{
  "categories":
  {
    "types": ["clothes", "shoes"],
    "gender": ["male", "female"]
  },
  "visible_data": ["types"],
  "data": [
    {
      "name": "Only male clothes",
      "position": [51.1, 17.05],
      "types": ["clothes"],
      "gender": ["male"]
    },
    {
      "name": "Clothes and shoes for males and females both",
      "position": [51.113, 17.06],
      "types": ["clothes", "shoes"],
      "gender": ["male", "female"]
    }
  ]
}
```
## Translation

To add/change language version based on `data`, the changes have to be done in: 
- config.yml 
- in translation folder (to each language version separately) within messages.po file
## Version History

### 0.1 - Initial Release - in development
#### 0.1.1 - In development
  * Using frontend served in npm  

#### 0.1.0 - First working version
 * JSON and Google hosted JSON database
 * Map displays points from database

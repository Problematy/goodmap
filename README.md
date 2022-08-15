![Github Actions](https://github.com/raven-wing/goodmap/actions/workflows/python-app.yml/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/Problematy/goodmap/badge.png)](https://coveralls.io/github/Problematy/goodmap)

# Good Map

Map engine to display any custom data ;)

## Tested on (other vesrion may not work / are not supported):

python (3.10)
poetry (1.1.13)
nodejs (12.22.9)
npm (8.3.1)

## Running App locally

### Application:

Local testing of the application requires a little different set of operations to execute, than what happens during production deployment (on gcp). So, to run locally the stack, execute in the same order:
* Rename config-template.yml to config.yml and change it's contents according to your needs. Values descriptions you can find inside config-template.yml.
* go to frontend directory
* install all dependencies with `npm install`
* build app by creating static file `npm run build`
* go to project directory
* use `poetry install`
* get into poetry shell `poetry shell`
* Run `FLASK_ENV=development;FLASK_APP=goodmap.goodmap flask run`

### Frontend:

If you want to run only fronted:
* go to frontend directory
* install all dependencies with `npm install`
* `npm run build` -- if you want to build app by creating static file (as in production envarioment)
* `npm run serve` -- if you want to run javasript server locally
* set `development_overwrites` for wanted endpoints, otherwise application will use compiled files.

### Backend:

If you want to run only backend:
All dependencies are specified in __pyproject.toml__ file. To install them in your onw environment:
* go to project directory
* use `poetry install`
* get into poetry shell `poetry shell`
* Run `FLASK_ENV=development;FLASK_APP=goodmap.goodmap flask run`

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

![Github Actions](https://github.com/raven-wing/goodmap/actions/workflows/python-app.yml/badge.svg)


# Good Map

Map engine to serve all the people ;) 

## Running App locally

### Configuration

Rename config-template.yml to config.yml and change it's contents according to your needs.
Values descriptions you can find inside config-template.yml.

### Backend 

All dependencies are specified in __pyproject.toml__ file. To install them in your onw environment:
* go to project directory
* use `poetry install`
* get into poetry shell `poetry shell`
* Run `FLASK_ENV=development;FLASK_APP=goodmap.goodmap flask run`

### Frontend (optional)
In production environment javascript is served as static files, but for ease of development you can run javascript
server locally:
* go to frontend directory
* install all dependencies with `nmp install`
* run server with `npm run serve`
* set `development_overwrites` for wanted endpoints, otherwise application will use compiled files.

##Database

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

## Version History

* 0.1
    * Initial Release - still in development

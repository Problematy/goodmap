![Github Actions](https://github.com/raven-wing/goodmap/actions/workflows/python-app.yml/badge.svg)


# Good Map

Map engine to serve all the people ;) 

## Getting Started

### Dependencies

All dependencies are specified in __pyproject.toml__ file. To install them in your onw environment:
* go to project directory
* use `poetry install`

### Running

* get into poetry shell `poetry shell`
* Run `DATA=<PATH-TO-DATA> FLASK_APP=goodmap.goodmap flask run` where __PATH_TO_DATA__ is json file with data format
specified below.
* You can add also __FLASK_ENV__ variable to get your development easier `FLASK_ENV=development` 


## Configuration

Configuration file is simple json file with list of objects containing:
* `categories` - categories of object on map (which later can be filtered based on)
* `data` - data about objects

### Categories
Fully configurable map where key is name of category and value is list of allowed types. E.g.
* "car_elements": ["mirror", "wheel", "steering wheel"]
* "color": ["red", "blue", "green"]

### Data
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

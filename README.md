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


## Data format

Data file is simple json file with list of objects containing:
* `data` - consisting data about objects
  * `name` - which is self explanatory
  * `position` - which contains coordinates on map
  * `types` - list of types(requirements) which object fits
* `types` - list of all available types
```
{
  "data": [
    {
      "name": "object1",
      "position": [51.1, 17.05],
      "types": ["clothes"]
    },
    {
      "name": "object2",
      "position": [51.113, 17.06],
      "types": ["clothes", "shoes"]
    }
  ],
  "types": ["clothes", "shoes"]
}
```

## Version History

* 0.1
    * Initial Release - still in development

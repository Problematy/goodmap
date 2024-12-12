import json
from functools import partial

from goodmap.core import get_queried_data

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


# ------------------------------------------------
# get_location_obligatory_fields


def json_db_get_location_obligatory_fields(db):
    return db.data["location_obligatory_fields"]


def json_file_db_get_location_obligatory_fields(db):
    with open(db.data_file_path, "r") as file:
        return json.load(file)["map"]["location_obligatory_fields"]


def google_json_db_get_location_obligatory_fields(db):
    return json.loads(db.blob.download_as_text(client=None))["map"]["location_obligatory_fields"]


def get_location_obligatory_fields(db):
    return globals()[f"{db.module_name}_get_location_obligatory_fields"](db)


# ------------------------------------------------
# get_data
def google_json_db_get_data(self):
    return json.loads(self.blob.download_as_text(client=None))["map"]


def json_file_db_get_data(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]


def json_db_get_data(self):
    return self.data


def get_data(db):
    return globals()[f"{db.module_name}_get_data"]


# ------------------------------------------------
# get_location


def get_location_from_raw_data(raw_data, uuid, location_model):
    point = next((point for point in raw_data["data"] if point["uuid"] == uuid), None)
    return location_model.model_validate(point) if point else None


def google_json_db_get_location(self, uuid, location_model):
    return get_location_from_raw_data(
        json.loads(self.blob.download_as_text(client=None))["map"], uuid, location_model
    )


def json_file_db_get_location(self, uuid, location_model):
    with open(self.data_file_path, "r") as file:
        point = get_location_from_raw_data(json.load(file)["map"], uuid, location_model)
        return point


def json_db_get_location(self, uuid, location_model):
    return get_location_from_raw_data(self.data, uuid, location_model)


def get_location(db, location_model):
    return partial(globals()[f"{db.module_name}_get_location"], location_model=location_model)


# ------------------------------------------------
# get_locations


def get_locations_list_from_raw_data(map_data, query, location_model):
    filtered_locations = get_queried_data(map_data["data"], map_data["categories"], query)
    return [location_model.model_validate(point) for point in filtered_locations]


def google_json_db_get_locations(self, query, location_model):
    return get_locations_list_from_raw_data(
        json.loads(self.blob.download_as_text(client=None))["map"], query, location_model
    )


def json_file_db_get_locations(self, query, location_model):
    with open(self.data_file_path, "r") as file:
        return get_locations_list_from_raw_data(json.load(file)["map"], query, location_model)


def json_db_get_locations(self, query, location_model):
    return get_locations_list_from_raw_data(self.data, query, location_model)


def get_locations(db, location_model):
    return partial(globals()[f"{db.module_name}_get_locations"], location_model=location_model)


# TODO extension function should be replaced with simple extend which would take a db plugin
# it could look like that:
#   `db.extend(goodmap_db_plugin)` in plugin all those functions would be organized


def extend_db_with_goodmap_queries(db, location_model):
    db.extend("get_data", get_data(db))
    db.extend("get_locations", get_locations(db, location_model))
    db.extend("get_location", get_location(db, location_model))
    return db

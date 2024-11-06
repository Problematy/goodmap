import json
from functools import partial

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution



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


def get_location_from_raw_data(raw_data, UUID, location_model):
    point = next((point for point in raw_data["data"] if point["UUID"] == UUID), None)
    return location_model.model_validate(point) if point else None


def google_json_db_get_location(self, UUID, location_model):
    return get_location_from_raw_data(
        json.loads(self.blob.download_as_text(client=None))["map"], UUID, location_model
    )


def json_file_db_get_location(self, UUID, location_model):
    with open(self.data_file_path, "r") as file:
        return get_location_from_raw_data(json.load(file)["map"], UUID, location_model)


def json_db_get_location(self, UUID, location_model):
    return get_location_from_raw_data(self.data, UUID, location_model)


def get_location(db, location_model):
    return partial(globals()[f"{db.module_name}_get_location"], location_model=location_model)


# ------------------------------------------------
# get_locations


def get_locations_list_from_raw_data(raw_data, location_model):
    return [location_model.model_validate(point) for point in raw_data["data"]]


def google_json_db_get_locations(self, location_model):
    return get_locations_list_from_raw_data(
        json.loads(self.blob.download_as_text(client=None))["map"], location_model
    )


def json_file_db_get_locations(self, location_model):
    with open(self.data_file_path, "r") as file:
        return get_locations_list_from_raw_data(json.load(file)["map"], location_model)


def json_db_get_locations(self, location_model):
    return get_locations_list_from_raw_data(self.data, location_model)


def get_locations(db, location_model):
    return partial(globals()[f"{db.module_name}_get_locations"], location_model=location_model)


#TODO extension function should be replaced with simple extend which would take a db plugin
3# it could look like that: `db.extend(goodmap_db_plugin)` in plugin all those functions would be organized
def goodmap_db_extended_app(db, location_model):
    db.extend("get_data", get_data(db))
    db.extend("get_locations", get_locations(db, location_model))
    db.extend("get_location", get_location(db, location_model))
    return db

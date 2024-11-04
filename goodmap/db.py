import json

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


#------------------------------------------------
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

#------------------------------------------------
# get_locations
def get_locations_list_from_raw_data(raw_data):
    return [{"position": point["position"], "UUID": point["UUID"]} for point in raw_data["data"]]

def google_json_db_get_locations(self):
    return get_locations_list_from_raw_data(json.loads(self.blob.download_as_text(client=None))["map"])

def json_file_db_get_locations(self):
    with open(self.data_file_path, "r") as file:
        return get_locations_list_from_raw_data(json.load(file)["map"])

def json_db_get_locations(self):
    return get_locations_list_from_raw_data(self.data)

def get_locations(db):
    return globals()[f"{db.module_name}_get_locations"]

#------------------------------------------------
# get_location

def get_location_from_raw_data(raw_data, UUID):
    return next((point for point in raw_data["data"] if point["UUID"] == UUID), None)

def google_json_db_get_location(self, UUID):
    return get_location_from_raw_data(json.loads(self.blob.download_as_text(client=None))["map"], UUID)

def json_file_db_get_location(self, UUID):
    with open(self.data_file_path, "r") as file:
        return get_location_from_raw_data(json.load(file)["map"], UUID)

def json_db_get_location(self, UUID):
    return get_location_from_raw_data(self.data, UUID)

def get_location(db):
    return globals()[f"{db.module_name}_get_location"]

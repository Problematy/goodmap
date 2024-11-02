import json

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


def google_json_db_get_data(self):
    raw_data = self.blob.download_as_text(client=None)
    return json.loads(raw_data)["map"]


def json_file_db_get_data(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]


def json_db_get_data(self):
    return self.data


def get_data(db):
    function_name = f"{db.module_name}_get_data"
    return globals()[function_name]


#--------------------------------------------
def get_points_list_from_raw_data(raw_data):
    data = raw_data["data"]
    return [{"position": point["position"], "UUID": point["UUID"]} for point in data]


def google_json_db_get_points(self):
    raw_data = self.blob.download_as_text(client=None)
    return get_points_list_from_raw_data(json.loads(raw_data)["map"])

def json_file_db_get_points(self):
    with open(self.data_file_path, "r") as file:
        return get_points_list_from_raw_data(json.load(file)["map"])

def json_db_get_points(self):
    return get_points_list_from_raw_data(self.data)


def get_points(db):
    function_name = f"{db.module_name}_get_points"
    return globals()[function_name]

#--------------------------------------------
def get_point_from_raw_data(raw_data, UUID):
    data = raw_data["data"]
    for point in data:
        if point["UUID"] == UUID:
            return point
    return None

def google_json_db_get_point(self, UUID):
    raw_data = self.blob.download_as_text(client=None)
    return get_point_from_raw_data(json.loads(raw_data)["map"], UUID)


def json_file_db_get_point(self, UUID):
    with open(self.data_file_path, "r") as file:
        return get_point_from_raw_data(json.load(file)["map"], UUID)

def json_db_get_point(self, UUID):
    return get_point_from_raw_data(self.data, UUID)


def get_point(db):
    function_name = f"{db.module_name}_get_point"
    return globals()[function_name]

import json
import os
import tempfile
from functools import partial

from goodmap.core import get_queried_data

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


def json_file_atomic_dump(data, file_path):
    dir_name = os.path.dirname(file_path)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as temp_file:
        json.dump(data, temp_file)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    os.replace(temp_file.name, file_path)


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


# ------------------------------------------------
# add_location


def json_file_db_add_location(self, location_data, location_model):
    location = location_model.model_validate(location_data)
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    map_data = json_file["map"].get("data", [])
    idx = next(
        (i for i, point in enumerate(map_data) if point.get("uuid") == location_data["uuid"]), None
    )
    if idx is not None:
        raise ValueError(f"Location with uuid {location_data['uuid']} already exists")

    map_data.append(location.model_dump())
    json_file["map"]["data"] = map_data

    json_file_atomic_dump(json_file, self.data_file_path)


def json_db_add_location(self, location_data, location_model):
    location = location_model.model_validate(location_data)
    idx = next(
        (
            i
            for i, point in enumerate(self.data.get("data", []))
            if point.get("uuid") == location_data["uuid"]
        ),
        None,
    )
    if idx is not None:
        raise ValueError(f"Location with uuid {location_data['uuid']} already exists")
    self.data["data"].append(location.model_dump())


def add_location(db, location_data, location_model):
    return globals()[f"{db.module_name}_add_location"](db, location_data, location_model)


# ------------------------------------------------
# update_location


def json_file_db_update_location(self, uuid, location_data, location_model):
    location = location_model.model_validate(location_data)
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    map_data = json_file["map"].get("data", [])
    idx = next((i for i, point in enumerate(map_data) if point.get("uuid") == uuid), None)
    if idx is None:
        raise ValueError(f"Location with uuid {uuid} not found")

    map_data[idx] = location.model_dump()
    json_file["map"]["data"] = map_data

    json_file_atomic_dump(json_file, self.data_file_path)


def json_db_update_location(self, uuid, location_data, location_model):
    location = location_model.model_validate(location_data)
    idx = next(
        (i for i, point in enumerate(self.data.get("data", [])) if point.get("uuid") == uuid), None
    )
    if idx is None:
        raise ValueError(f"Location with uuid {uuid} not found")
    self.data["data"][idx] = location.model_dump()


def update_location(db, uuid, location_data, location_model):
    return globals()[f"{db.module_name}_update_location"](db, uuid, location_data, location_model)


# ------------------------------------------------
# delete_location


def json_file_db_delete_location(self, uuid):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    map_data = json_file["map"].get("data", [])
    idx = next((i for i, point in enumerate(map_data) if point.get("uuid") == uuid), None)
    if idx is None:
        raise ValueError(f"Location with uuid {uuid} not found")

    del map_data[idx]
    json_file["map"]["data"] = map_data

    json_file_atomic_dump(json_file, self.data_file_path)


def json_db_delete_location(self, uuid):
    idx = next(
        (i for i, point in enumerate(self.data.get("data", [])) if point.get("uuid") == uuid), None
    )
    if idx is None:
        raise ValueError(f"Location with uuid {uuid} not found")
    del self.data["data"][idx]


def delete_location(db, uuid):
    return globals()[f"{db.module_name}_delete_location"](db, uuid)


# ------------------------------------------------
# add_suggestion


def json_db_add_suggestion(self, suggestion_data):
    suggestions = self.data.setdefault("suggestions", [])
    if any(s.get("uuid") == suggestion_data.get("uuid") for s in suggestions):
        raise ValueError(f"Suggestion with uuid {suggestion_data['uuid']} already exists")

    record = dict(suggestion_data)
    record["status"] = "pending"
    suggestions.append(record)


def json_file_db_add_suggestion(self, suggestion_data):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    suggestions = json_file["map"].get("suggestions", [])
    if any(s.get("uuid") == suggestion_data.get("uuid") for s in suggestions):
        raise ValueError(f"Suggestion with uuid {suggestion_data['uuid']} already exists")

    record = dict(suggestion_data)
    record["status"] = "pending"
    suggestions.append(record)
    json_file["map"]["suggestions"] = suggestions

    json_file_atomic_dump(json_file, self.data_file_path)


def add_suggestion(db, suggestion_data):
    return globals()[f"{db.module_name}_add_suggestion"](db, suggestion_data)


# ------------------------------------------------
# get_suggestions


def json_db_get_suggestions(self, query_params):
    suggestions = self.data.get("suggestions", [])

    statuses = query_params.get("status")
    if statuses:
        suggestions = [s for s in suggestions if s.get("status") in statuses]

    return suggestions


def json_file_db_get_suggestions(self, query_params):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    suggestions = json_file["map"].get("suggestions", [])

    statuses = query_params.get("status")
    if statuses:
        suggestions = [s for s in suggestions if s.get("status") in statuses]

    return suggestions


def get_suggestions(db):
    return globals()[f"{db.module_name}_get_suggestions"]


# ------------------------------------------------
# get_suggestion


def json_db_get_suggestion(self, suggestion_id):
    return next(
        (s for s in self.data.get("suggestions", []) if s.get("uuid") == suggestion_id), None
    )


def json_file_db_get_suggestion(self, suggestion_id):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)
    return next(
        (s for s in json_file["map"].get("suggestions", []) if s.get("uuid") == suggestion_id), None
    )


def get_suggestion(db):
    return globals()[f"{db.module_name}_get_suggestion"]


# ------------------------------------------------
# update_suggestion


def json_db_update_suggestion(self, suggestion_id, status):
    suggestions = self.data.get("suggestions", [])
    for s in suggestions:
        if s.get("uuid") == suggestion_id:
            s["status"] = status
            return
    raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def json_file_db_update_suggestion(self, suggestion_id, status):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    suggestions = json_file["map"].get("suggestions", [])
    for s in suggestions:
        if s.get("uuid") == suggestion_id:
            s["status"] = status
            break
    else:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")

    json_file["map"]["suggestions"] = suggestions

    json_file_atomic_dump(json_file, self.data_file_path)


def update_suggestion(db, suggestion_id, status):
    return globals()[f"{db.module_name}_update_suggestion"](db, suggestion_id, status)


# ------------------------------------------------
# delete_suggestion


def json_db_delete_suggestion(self, suggestion_id):
    suggestions = self.data.get("suggestions", [])
    idx = next((i for i, s in enumerate(suggestions) if s.get("uuid") == suggestion_id), None)
    if idx is None:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")

    del suggestions[idx]


def json_file_db_delete_suggestion(self, suggestion_id):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    suggestions = json_file["map"].get("suggestions", [])
    idx = next((i for i, s in enumerate(suggestions) if s.get("uuid") == suggestion_id), None)
    if idx is None:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")

    del suggestions[idx]
    json_file["map"]["suggestions"] = suggestions

    json_file_atomic_dump(json_file, self.data_file_path)


def delete_suggestion(db, suggestion_id):
    return globals()[f"{db.module_name}_delete_suggestion"](db, suggestion_id)


# ------------------------------------------------
# add_report


def json_db_add_report(self, report_data):
    reports = self.data.setdefault("reports", [])
    if any(r.get("uuid") == report_data.get("uuid") for r in reports):
        raise ValueError(f"Report with uuid {report_data['uuid']} already exists")

    reports.append(report_data)


def json_file_db_add_report(self, report_data):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    reports = json_file["map"].get("reports", [])
    if any(r.get("uuid") == report_data.get("uuid") for r in reports):
        raise ValueError(f"Report with uuid {report_data['uuid']} already exists")

    reports.append(report_data)
    json_file["map"]["reports"] = reports

    json_file_atomic_dump(json_file, self.data_file_path)


def add_report(db, report_data):
    return globals()[f"{db.module_name}_add_report"](db, report_data)


# ------------------------------------------------
# get_reports


def json_db_get_reports(self, query_params):
    reports = self.data.get("reports", [])

    statuses = query_params.get("status")
    if statuses:
        reports = [r for r in reports if r.get("status") in statuses]

    priorities = query_params.get("priority")
    if priorities:
        reports = [r for r in reports if r.get("priority") in priorities]

    return reports


def json_file_db_get_reports(self, query_params):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    reports = json_file["map"].get("reports", [])

    statuses = query_params.get("status")
    if statuses:
        reports = [r for r in reports if r.get("status") in statuses]

    priorities = query_params.get("priority")
    if priorities:
        reports = [r for r in reports if r.get("priority") in priorities]

    return reports


def get_reports(db):
    return globals()[f"{db.module_name}_get_reports"]


# ------------------------------------------------
# get_report


def json_db_get_report(self, report_id):
    return next((r for r in self.data.get("reports", []) if r.get("uuid") == report_id), None)


def json_file_db_get_report(self, report_id):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    return next(
        (r for r in json_file["map"].get("reports", []) if r.get("uuid") == report_id), None
    )


def get_report(db):
    return globals()[f"{db.module_name}_get_report"]


# ------------------------------------------------
# update_report


def json_db_update_report(self, report_id, status=None, priority=None):
    reports = self.data.get("reports", [])
    for r in reports:
        if r.get("uuid") == report_id:
            if status:
                r["status"] = status
            if priority:
                r["priority"] = priority
            return
    raise ValueError(f"Report with uuid {report_id} not found")


def json_file_db_update_report(self, report_id, status=None, priority=None):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    reports = json_file["map"].get("reports", [])
    for r in reports:
        if r.get("uuid") == report_id:
            if status:
                r["status"] = status
            if priority:
                r["priority"] = priority
            break
    else:
        raise ValueError(f"Report with uuid {report_id} not found")

    json_file["map"]["reports"] = reports

    json_file_atomic_dump(json_file, self.data_file_path)


def update_report(db, report_id, status=None, priority=None):
    return globals()[f"{db.module_name}_update_report"](db, report_id, status, priority)


# ------------------------------------------------
# delete_report


def json_db_delete_report(self, report_id):
    reports = self.data.get("reports", [])
    idx = next((i for i, r in enumerate(reports) if r.get("uuid") == report_id), None)
    if idx is None:
        raise ValueError(f"Report with uuid {report_id} not found")
    del reports[idx]


def json_file_db_delete_report(self, report_id):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    reports = json_file["map"].get("reports", [])
    idx = next((i for i, r in enumerate(reports) if r.get("uuid") == report_id), None)
    if idx is None:
        raise ValueError(f"Report with uuid {report_id} not found")

    del reports[idx]
    json_file["map"]["reports"] = reports

    json_file_atomic_dump(json_file, self.data_file_path)


def delete_report(db, report_id):
    return globals()[f"{db.module_name}_delete_report"](db, report_id)


# TODO extension function should be replaced with simple extend which would take a db plugin
# it could look like that:
#   `db.extend(goodmap_db_plugin)` in plugin all those functions would be organized


def extend_db_with_goodmap_queries(db, location_model):
    db.extend("get_data", get_data(db))
    db.extend("get_locations", get_locations(db, location_model))
    db.extend("get_location", get_location(db, location_model))
    db.extend("add_location", partial(add_location, location_model=location_model))
    db.extend("update_location", partial(update_location, location_model=location_model))
    db.extend("delete_location", delete_location)
    if db.module_name in ("json_db", "json_file_db"):
        db.extend("add_suggestion", add_suggestion)
        db.extend("get_suggestions", get_suggestions(db))
        db.extend("get_suggestion", get_suggestion(db))
        db.extend("update_suggestion", update_suggestion)
        db.extend("delete_suggestion", delete_suggestion)
        db.extend("add_report", add_report)
        db.extend("get_reports", get_reports(db))
        db.extend("get_report", get_report(db))
        db.extend("update_report", update_report)
        db.extend("delete_report", delete_report)
    return db

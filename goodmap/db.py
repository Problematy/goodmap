import json
import os
import tempfile
from functools import partial
from typing import Any

from goodmap.core import get_queried_data
from goodmap.data_models.location import LocationBase

# TODO file is temporary solution to be compatible with old, static code,
#  it should be replaced with dynamic solution


def __parse_pagination_params(query):
    """Extract and validate pagination parameters from query."""
    try:
        page = max(1, int(query.get("page", ["1"])[0]))
    except (ValueError, IndexError, TypeError):
        page = 1

    per_page_raw = query.get("per_page", ["20"])[0] if query.get("per_page") else "20"
    if per_page_raw == "all":
        per_page = None
    else:
        try:
            per_page = max(1, min(int(per_page_raw), 1000))  # Cap at 1000
        except (ValueError, TypeError):
            per_page = 20

    sort_by = query.get("sort_by", [None])[0]
    sort_order = query.get("sort_order", ["asc"])[0] if query.get("sort_order") else "asc"

    return page, per_page, sort_by, sort_order.lower()


def __build_pagination_response(items, total, page, per_page):
    """Build standardized pagination response."""
    if per_page:
        total_pages = (total + per_page - 1) // per_page
    else:
        total_pages = 1
        per_page = total

    return {
        "items": items,
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        },
    }


def json_file_atomic_dump(data, file_path):
    dir_name = os.path.dirname(file_path)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as temp_file:
        json.dump(data, temp_file)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    os.replace(temp_file.name, file_path)


class PaginationHelper:
    """Common pagination utility to eliminate duplication across backends."""

    @staticmethod
    def get_sort_key(item, sort_by):
        """Extract sort key from item for both dict and object types."""
        if sort_by == "name" and hasattr(item, "name"):
            value = item.name
        elif isinstance(item, dict):
            value = item.get(sort_by)
        else:
            value = getattr(item, sort_by, None)
        return (value is not None, value or "")

    @staticmethod
    def apply_pagination_and_sorting(items, page, per_page, sort_by, sort_order):
        """Apply sorting and pagination to a list of items."""
        # Apply sorting
        if sort_by:
            reverse = sort_order == "desc"
            items.sort(
                key=lambda item: PaginationHelper.get_sort_key(item, sort_by), reverse=reverse  # type: ignore
            )

        total_count = len(items)

        # Apply pagination
        if per_page:
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_items = items[start_idx:end_idx]
        else:
            paginated_items = items

        return paginated_items, total_count

    @staticmethod
    def apply_filters(items, filters):
        """Apply filtering based on provided filters dictionary."""
        filtered_items = items

        # Apply status filtering
        if "status" in filters:
            statuses = filters["status"]
            if statuses:
                filtered_items = [
                    item
                    for item in filtered_items
                    if (
                        item.get("status")
                        if isinstance(item, dict)
                        else getattr(item, "status", None)
                    )
                    in statuses
                ]

        # Apply priority filtering
        if "priority" in filters:
            priorities = filters["priority"]
            if priorities:
                filtered_items = [
                    item
                    for item in filtered_items
                    if (
                        item.get("priority")
                        if isinstance(item, dict)
                        else getattr(item, "priority", None)
                    )
                    in priorities
                ]

        return filtered_items

    @staticmethod
    def serialize_items(items):
        """Convert items to dict if needed (for location models)."""
        if items and hasattr(items[0], "model_dump"):
            return [x.model_dump() for x in items]
        else:
            return items

    @staticmethod
    def create_paginated_response(items, query, extract_filters_func=None):
        """Create a complete paginated response with all common logic."""
        # Parse pagination parameters using the existing function
        try:
            page = max(1, int(query.get("page", ["1"])[0]))
        except (ValueError, IndexError, TypeError):
            page = 1

        per_page_raw = query.get("per_page", ["20"])[0] if query.get("per_page") else "20"
        if per_page_raw == "all":
            per_page = None
        else:
            try:
                per_page = max(1, min(int(per_page_raw), 1000))  # Cap at 1000
            except (ValueError, TypeError):
                per_page = 20

        sort_by = query.get("sort_by", [None])[0]
        sort_order = query.get("sort_order", ["asc"])[0] if query.get("sort_order") else "asc"
        sort_order = sort_order.lower()

        # Apply filters if any
        filters = {}
        if query:
            if "status" in query:
                filters["status"] = query["status"]
            if "priority" in query:
                filters["priority"] = query["priority"]

        # Allow custom filter extraction
        if extract_filters_func:
            custom_filters = extract_filters_func(query)
            filters.update(custom_filters)

        if filters:
            items = PaginationHelper.apply_filters(items, filters)

        # Apply pagination and sorting
        paginated_items, total_count = PaginationHelper.apply_pagination_and_sorting(
            items, page, per_page, sort_by, sort_order
        )

        # Serialize items if needed
        serialized_items = PaginationHelper.serialize_items(paginated_items)

        # Build pagination response directly
        if per_page:
            total_pages = (total_count + per_page - 1) // per_page
        else:
            total_pages = 1
            per_page = total_count

        return {
            "items": serialized_items,
            "pagination": {
                "total": total_count,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            },
        }


class FileIOHelper:
    """Common file I/O utilities to eliminate duplication."""

    @staticmethod
    def read_json_file(file_path):
        """Read and parse JSON file."""
        with open(file_path, "r") as file:
            return json.load(file)

    @staticmethod
    def write_json_file_atomic(data, file_path):
        """Write JSON data to file atomically."""
        json_file_atomic_dump(data, file_path)

    @staticmethod
    def get_data_from_file(file_path, data_key="map"):
        """Get data from JSON file with specified key structure."""
        json_data = FileIOHelper.read_json_file(file_path)
        return json_data.get(data_key, {})


class ErrorHelper:
    """Common error handling utilities."""

    @staticmethod
    def raise_already_exists_error(item_type, uuid):
        """Raise standardized 'already exists' error."""
        raise ValueError(f"{item_type} with uuid {uuid} already exists")

    @staticmethod
    def raise_not_found_error(item_type, uuid):
        """Raise standardized 'not found' error."""
        raise ValueError(f"{item_type} with uuid {uuid} not found")

    @staticmethod
    def check_item_exists(items, uuid, item_type):
        """Check if item with UUID exists and raise error if it does."""
        existing = next(
            (
                item
                for item in items
                if (item.get("uuid") if isinstance(item, dict) else getattr(item, "uuid", None))
                == uuid
            ),
            None,
        )
        if existing:
            ErrorHelper.raise_already_exists_error(item_type, uuid)

    @staticmethod
    def find_item_by_uuid(items, uuid, item_type):
        """Find item by UUID and raise error if not found."""
        item = next(
            (
                item
                for item in items
                if (item.get("uuid") if isinstance(item, dict) else getattr(item, "uuid", None))
                == uuid
            ),
            None,
        )
        if not item:
            ErrorHelper.raise_not_found_error(item_type, uuid)
        return item


class CRUDHelper:
    """Common CRUD operation utilities to eliminate duplication."""

    @staticmethod
    def add_item_to_json_db(db_data, collection_name, item_data, default_status=None):
        """Add item to JSON in-memory database."""
        collection = db_data.setdefault(collection_name, [])
        ErrorHelper.check_item_exists(
            collection, item_data.get("uuid"), collection_name.rstrip("s").capitalize()
        )

        record = dict(item_data)
        if default_status:
            record["status"] = default_status
        collection.append(record)

    @staticmethod
    def add_item_to_json_file_db(file_path, collection_name, item_data, default_status=None):
        """Add item to JSON file database."""
        json_file = FileIOHelper.read_json_file(file_path)
        collection = json_file["map"].get(collection_name, [])

        ErrorHelper.check_item_exists(
            collection, item_data.get("uuid"), collection_name.rstrip("s").capitalize()
        )

        record = dict(item_data)
        if default_status:
            record["status"] = default_status
        collection.append(record)
        json_file["map"][collection_name] = collection

        FileIOHelper.write_json_file_atomic(json_file, file_path)

    @staticmethod
    def add_item_to_mongodb(db_collection, item_data, item_type, default_status=None):
        """Add item to MongoDB database."""
        existing = db_collection.find_one({"uuid": item_data.get("uuid")})
        if existing:
            ErrorHelper.raise_already_exists_error(item_type, item_data.get("uuid"))

        record = dict(item_data)
        if default_status:
            record["status"] = default_status
        db_collection.insert_one(record)


# ------------------------------------------------
# get_location_obligatory_fields


def json_db_get_location_obligatory_fields(db):
    return db.data["location_obligatory_fields"]


def json_file_db_get_location_obligatory_fields(db):
    with open(db.data_file_path, "r") as file:
        return json.load(file)["map"]["location_obligatory_fields"]


def google_json_db_get_location_obligatory_fields(db):
    return json.loads(db.blob.download_as_text(client=None))["map"]["location_obligatory_fields"]


def mongodb_db_get_location_obligatory_fields(db):
    config_doc = db.db.config.find_one({"_id": "map_config"})
    if config_doc and "location_obligatory_fields" in config_doc:
        return config_doc["location_obligatory_fields"]
    return []


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


def mongodb_db_get_data(self):
    config_doc = self.db.config.find_one({"_id": "map_config"})
    if config_doc:
        return {
            "data": list(self.db.locations.find({}, {"_id": 0})),
            "categories": config_doc.get("categories", {}),
            "location_obligatory_fields": config_doc.get("location_obligatory_fields", []),
            # Backward-compat keys expected by core_api today
            "visible_data": config_doc.get("visible_data", {}),
            "meta_data": config_doc.get("meta_data", {}),
        }
    return {
        "data": [],
        "categories": {},
        "location_obligatory_fields": [],
        "visible_data": {},
        "meta_data": {},
    }


def get_data(db):
    return globals()[f"{db.module_name}_get_data"]


# ------------------------------------------------
# get_visible_data


def google_json_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from Google Cloud Storage JSON blob.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if not found.
    """
    return self.data.get("map", {}).get("visible_data", {})


def json_file_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from JSON file database.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if not found.
    """
    return self.data.get("map", {}).get("visible_data", {})


def json_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from in-memory JSON database.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if not found.
    """
    return self.data.get("visible_data", {})


def mongodb_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from MongoDB.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if config document not found or field missing.

    Raises:
        pymongo.errors.ConnectionFailure: If database connection fails.
        pymongo.errors.OperationFailure: If database operation fails.
    """
    config_doc = self.db.config.find_one({"_id": "map_config"})
    if config_doc:
        return config_doc.get("visible_data", {})
    return {}


def get_visible_data(db):
    """
    Get the appropriate get_visible_data function for the given database backend.

    Args:
        db: Database instance (must have module_name attribute).

    Returns:
        callable: Backend-specific get_visible_data function.
    """
    return globals()[f"{db.module_name}_get_visible_data"]


# ------------------------------------------------
# get_meta_data


def google_json_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from Google Cloud Storage JSON blob.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if not found.
    """
    return self.data.get("map", {}).get("meta_data", {})


def json_file_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from JSON file database.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if not found.
    """
    return self.data.get("map", {}).get("meta_data", {})


def json_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from in-memory JSON database.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if not found.
    """
    return self.data.get("meta_data", {})


def mongodb_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from MongoDB.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if config document not found or field missing.

    Raises:
        pymongo.errors.ConnectionFailure: If database connection fails.
        pymongo.errors.OperationFailure: If database operation fails.
    """
    config_doc = self.db.config.find_one({"_id": "map_config"})
    if config_doc:
        return config_doc.get("meta_data", {})
    return {}


def get_meta_data(db):
    """
    Get the appropriate get_meta_data function for the given database backend.

    Args:
        db: Database instance (must have module_name attribute).

    Returns:
        callable: Backend-specific get_meta_data function.
    """
    return globals()[f"{db.module_name}_get_meta_data"]


# ------------------------------------------------
# get_categories


def json_db_get_categories(self):
    return self.data["categories"].keys()


def json_file_db_get_categories(self):
    with open(self.data_file_path, "r") as file:
        return json.load(file)["map"]["categories"].keys()


def google_json_db_get_categories(self):
    return json.loads(self.blob.download_as_text(client=None))["map"]["categories"].keys()


def mongodb_db_get_categories(self):
    config_doc = self.db.config.find_one({"_id": "map_config"})
    if config_doc and "categories" in config_doc:
        return list(config_doc["categories"].keys())
    return []


def get_categories(db):
    return globals()[f"{db.module_name}_get_categories"]


# ------------------------------------------------
# get_category_data


def json_db_get_category_data(self, category_type=None):
    if category_type:
        return {
            "categories": {category_type: self.data["categories"].get(category_type, [])},
            "categories_help": self.data.get("categories_help", []),
            "categories_options_help": {
                category_type: self.data.get("categories_options_help", {}).get(category_type, [])
            },
        }
    return {
        "categories": self.data["categories"],
        "categories_help": self.data.get("categories_help", []),
        "categories_options_help": self.data.get("categories_options_help", {}),
    }


def json_file_db_get_category_data(self, category_type=None):
    with open(self.data_file_path, "r") as file:
        data = json.load(file)["map"]
        if category_type:
            return {
                "categories": {category_type: data["categories"].get(category_type, [])},
                "categories_help": data.get("categories_help", []),
                "categories_options_help": {
                    category_type: data.get("categories_options_help", {}).get(category_type, [])
                },
            }
        return {
            "categories": data["categories"],
            "categories_help": data.get("categories_help", []),
            "categories_options_help": data.get("categories_options_help", {}),
        }


def google_json_db_get_category_data(self, category_type=None):
    data = json.loads(self.blob.download_as_text(client=None))["map"]
    if category_type:
        return {
            "categories": {category_type: data["categories"].get(category_type, [])},
            "categories_help": data.get("categories_help", []),
            "categories_options_help": {
                category_type: data.get("categories_options_help", {}).get(category_type, [])
            },
        }
    return {
        "categories": data["categories"],
        "categories_help": data.get("categories_help", []),
        "categories_options_help": data.get("categories_options_help", {}),
    }


def mongodb_db_get_category_data(self, category_type=None):
    config_doc = self.db.config.find_one({"_id": "map_config"})
    if config_doc:
        if category_type:
            return {
                "categories": {
                    category_type: config_doc.get("categories", {}).get(category_type, [])
                },
                "categories_help": config_doc.get("categories_help", []),
                "categories_options_help": {
                    category_type: config_doc.get("categories_options_help", {}).get(
                        category_type, []
                    )
                },
            }
        return {
            "categories": config_doc.get("categories", {}),
            "categories_help": config_doc.get("categories_help", []),
            "categories_options_help": config_doc.get("categories_options_help", {}),
        }
    return {"categories": {}, "categories_help": [], "categories_options_help": {}}


def get_category_data(db):
    return globals()[f"{db.module_name}_get_category_data"]


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


def mongodb_db_get_location(self, uuid, location_model):
    location_doc = self.db.locations.find_one({"uuid": uuid}, {"_id": 0})
    return location_model.model_validate(location_doc) if location_doc else None


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


def mongodb_db_get_locations(self, query, location_model):
    mongo_query = {}
    for key, values in query.items():
        if values:
            mongo_query[key] = {"$in": values}

    projection = {"_id": 0, "uuid": 1, "position": 1, "remark": 1}
    data = self.db.locations.find(mongo_query, projection)
    return (LocationBase.model_validate(loc) for loc in data)


def get_locations(db, location_model):
    return partial(globals()[f"{db.module_name}_get_locations"], location_model=location_model)


def google_json_db_get_locations_paginated(self, query, location_model):
    """Google JSON locations with improved pagination."""
    # Get all locations from raw data
    data = json.loads(self.blob.download_as_text(client=None))["map"]
    all_locations = list(get_locations_list_from_raw_data(data, query, location_model))
    return PaginationHelper.create_paginated_response(all_locations, query)


def json_db_get_locations_paginated(self, query, location_model):
    """JSON locations with improved pagination."""
    # Get all locations from raw data
    all_locations = list(get_locations_list_from_raw_data(self.data, query, location_model))
    return PaginationHelper.create_paginated_response(all_locations, query)


def json_file_db_get_locations_paginated(self, query, location_model):
    """JSON file locations with improved pagination."""
    data = FileIOHelper.get_data_from_file(self.data_file_path)
    # Get all locations from raw data
    all_locations = list(get_locations_list_from_raw_data(data, query, location_model))
    return PaginationHelper.create_paginated_response(all_locations, query)


def mongodb_db_get_locations_paginated(self, query, location_model):
    """MongoDB locations with improved pagination."""
    page, per_page, sort_by, sort_order = __parse_pagination_params(query)

    # Build MongoDB query
    mongo_query = {}
    for key, values in query.items():
        if values:
            mongo_query[key] = {"$in": values}

    # Get total count
    total_count = self.db.locations.count_documents(mongo_query)

    # Build aggregation pipeline
    pipeline = [{"$match": mongo_query}]

    # Add sorting
    if sort_by:
        sort_direction = -1 if sort_order == "desc" else 1
        pipeline.append({"$sort": {sort_by: sort_direction}})

    # Add pagination
    if per_page:
        pipeline.extend([{"$skip": (page - 1) * per_page}, {"$limit": per_page}])  # type: ignore

    # Remove MongoDB _id field
    pipeline.append({"$project": {"_id": 0}})

    # Execute query
    cursor = self.db.locations.aggregate(pipeline)
    locations = [location_model.model_validate(loc) for loc in cursor]

    # Convert items to dict if needed (for location models)
    if locations and hasattr(locations[0], "model_dump"):
        serialized_locations = [x.model_dump() for x in locations]
    else:
        serialized_locations = locations

    return __build_pagination_response(serialized_locations, total_count, page, per_page)


def get_locations_paginated(db, location_model):
    return partial(
        globals()[f"{db.module_name}_get_locations_paginated"], location_model=location_model
    )


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


def mongodb_db_add_location(self, location_data, location_model):
    location = location_model.model_validate(location_data)
    existing = self.db.locations.find_one({"uuid": location_data["uuid"]})
    if existing:
        raise ValueError(f"Location with uuid {location_data['uuid']} already exists")
    self.db.locations.insert_one(location.model_dump())


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


def mongodb_db_update_location(self, uuid, location_data, location_model):
    location = location_model.model_validate(location_data)
    result = self.db.locations.update_one({"uuid": uuid}, {"$set": location.model_dump()})
    if result.matched_count == 0:
        raise ValueError(f"Location with uuid {uuid} not found")


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


def mongodb_db_delete_location(self, uuid):
    result = self.db.locations.delete_one({"uuid": uuid})
    if result.deleted_count == 0:
        raise ValueError(f"Location with uuid {uuid} not found")


def delete_location(db, uuid):
    return globals()[f"{db.module_name}_delete_location"](db, uuid)


# ------------------------------------------------
# add_suggestion


def json_db_add_suggestion(self, suggestion_data):
    CRUDHelper.add_item_to_json_db(self.data, "suggestions", suggestion_data, "pending")


def json_file_db_add_suggestion(self, suggestion_data):
    CRUDHelper.add_item_to_json_file_db(
        self.data_file_path, "suggestions", suggestion_data, "pending"
    )


def mongodb_db_add_suggestion(self, suggestion_data):
    CRUDHelper.add_item_to_mongodb(self.db.suggestions, suggestion_data, "Suggestion", "pending")


def google_json_db_add_suggestion(self, suggestion_data):
    # Temporary workaround: just use notifier without storing
    # Full implementation would require writing back to Google Cloud Storage
    pass


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


def json_db_get_suggestions_paginated(self, query):
    """JSON suggestions with improved pagination."""
    suggestions = self.data.get("suggestions", [])
    return PaginationHelper.create_paginated_response(suggestions, query)


def json_file_db_get_suggestions(self, query_params):
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    suggestions = json_file["map"].get("suggestions", [])

    statuses = query_params.get("status")
    if statuses:
        suggestions = [s for s in suggestions if s.get("status") in statuses]

    return suggestions


def json_file_db_get_suggestions_paginated(self, query):
    """JSON file suggestions with improved pagination."""
    with open(self.data_file_path, "r") as file:
        json_file = json.load(file)

    suggestions = json_file["map"].get("suggestions", [])
    return PaginationHelper.create_paginated_response(suggestions, query)


def mongodb_db_get_suggestions(self, query_params):
    query = {}
    statuses = query_params.get("status")
    if statuses:
        query["status"] = {"$in": statuses}

    return list(self.db.suggestions.find(query, {"_id": 0}))


def mongodb_db_get_suggestions_paginated(self, query):
    """MongoDB suggestions with improved pagination."""
    page, per_page, sort_by, sort_order = __parse_pagination_params(query)

    # Build MongoDB query
    mongo_query = {}
    statuses = query.get("status")
    if statuses:
        mongo_query["status"] = {"$in": statuses}

    # Get total count
    total_count = self.db.suggestions.count_documents(mongo_query)

    # Build aggregation pipeline
    pipeline = [{"$match": mongo_query}]

    # Add sorting
    if sort_by:
        sort_direction = -1 if sort_order == "desc" else 1
        pipeline.append({"$sort": {sort_by: sort_direction}})

    # Add pagination
    if per_page:
        pipeline.extend([{"$skip": (page - 1) * per_page}, {"$limit": per_page}])  # type: ignore

    # Remove MongoDB _id field
    pipeline.append({"$project": {"_id": 0}})

    # Execute query
    cursor = self.db.suggestions.aggregate(pipeline)
    items = list(cursor)

    return __build_pagination_response(items, total_count, page, per_page)


def google_json_db_get_suggestions(self, query_params):
    # GoogleJsonDb is read-only, suggestions not stored in blob
    return []


def google_json_db_get_suggestions_paginated(self, query):
    """Google JSON suggestions with pagination (read-only)."""
    return PaginationHelper.create_paginated_response([], query)


def get_suggestions(db):
    return globals()[f"{db.module_name}_get_suggestions"]


def get_suggestions_paginated(db):
    return globals()[f"{db.module_name}_get_suggestions_paginated"]


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


def mongodb_db_get_suggestion(self, suggestion_id):
    return self.db.suggestions.find_one({"uuid": suggestion_id}, {"_id": 0})


def google_json_db_get_suggestion(self, suggestion_id):
    # GoogleJsonDb is read-only, suggestions not stored in blob
    return None


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


def mongodb_db_update_suggestion(self, suggestion_id, status):
    result = self.db.suggestions.update_one({"uuid": suggestion_id}, {"$set": {"status": status}})
    if result.matched_count == 0:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def google_json_db_update_suggestion(self, suggestion_id, status):
    # GoogleJsonDb is read-only, no-op
    pass


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


def mongodb_db_delete_suggestion(self, suggestion_id):
    result = self.db.suggestions.delete_one({"uuid": suggestion_id})
    if result.deleted_count == 0:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def google_json_db_delete_suggestion(self, suggestion_id):
    # GoogleJsonDb is read-only, no-op
    pass


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


def mongodb_db_add_report(self, report_data):
    existing = self.db.reports.find_one({"uuid": report_data.get("uuid")})
    if existing:
        raise ValueError(f"Report with uuid {report_data['uuid']} already exists")

    self.db.reports.insert_one(report_data)


def google_json_db_add_report(self, report_data):
    # Temporary workaround: just use notifier without storing
    # Full implementation would require writing back to Google Cloud Storage
    pass


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


def json_db_get_reports_paginated(self, query):
    """JSON reports with improved pagination."""
    reports = self.data.get("reports", [])
    return PaginationHelper.create_paginated_response(reports, query)


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


def json_file_db_get_reports_paginated(self, query):
    """JSON file reports with improved pagination."""
    data = FileIOHelper.get_data_from_file(self.data_file_path)
    reports = data.get("reports", [])
    return PaginationHelper.create_paginated_response(reports, query)


def mongodb_db_get_reports(self, query_params):
    query = {}

    statuses = query_params.get("status")
    if statuses:
        query["status"] = {"$in": statuses}

    priorities = query_params.get("priority")
    if priorities:
        query["priority"] = {"$in": priorities}

    return list(self.db.reports.find(query, {"_id": 0}))


def mongodb_db_get_reports_paginated(self, query):
    """MongoDB reports with improved pagination."""
    page, per_page, sort_by, sort_order = __parse_pagination_params(query)

    # Build MongoDB query
    mongo_query = {}

    statuses = query.get("status")
    if statuses:
        mongo_query["status"] = {"$in": statuses}

    priorities = query.get("priority")
    if priorities:
        mongo_query["priority"] = {"$in": priorities}

    # Get total count
    total_count = self.db.reports.count_documents(mongo_query)

    # Build aggregation pipeline
    pipeline = [{"$match": mongo_query}]

    # Add sorting
    if sort_by:
        sort_direction = -1 if sort_order == "desc" else 1
        pipeline.append({"$sort": {sort_by: sort_direction}})

    # Add pagination
    if per_page:
        pipeline.extend([{"$skip": (page - 1) * per_page}, {"$limit": per_page}])  # type: ignore

    # Remove MongoDB _id field
    pipeline.append({"$project": {"_id": 0}})

    # Execute query
    cursor = self.db.reports.aggregate(pipeline)
    items = list(cursor)

    return __build_pagination_response(items, total_count, page, per_page)


def google_json_db_get_reports(self, query_params):
    # GoogleJsonDb is read-only, reports not stored in blob
    return []


def google_json_db_get_reports_paginated(self, query):
    """Google JSON reports with pagination (read-only)."""
    return PaginationHelper.create_paginated_response([], query)


def get_reports(db):
    return globals()[f"{db.module_name}_get_reports"]


def get_reports_paginated(db):
    return globals()[f"{db.module_name}_get_reports_paginated"]


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


def mongodb_db_get_report(self, report_id):
    return self.db.reports.find_one({"uuid": report_id}, {"_id": 0})


def google_json_db_get_report(self, report_id):
    # GoogleJsonDb is read-only, reports not stored in blob
    return None


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


def mongodb_db_update_report(self, report_id, status=None, priority=None):
    update_doc = {}
    if status:
        update_doc["status"] = status
    if priority:
        update_doc["priority"] = priority

    if update_doc:
        result = self.db.reports.update_one({"uuid": report_id}, {"$set": update_doc})
        if result.matched_count == 0:
            raise ValueError(f"Report with uuid {report_id} not found")


def google_json_db_update_report(self, report_id, status=None, priority=None):
    # GoogleJsonDb is read-only, no-op
    pass


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


def mongodb_db_delete_report(self, report_id):
    result = self.db.reports.delete_one({"uuid": report_id})
    if result.deleted_count == 0:
        raise ValueError(f"Report with uuid {report_id} not found")


def google_json_db_delete_report(self, report_id):
    # GoogleJsonDb is read-only, no-op
    pass


def delete_report(db, report_id):
    return globals()[f"{db.module_name}_delete_report"](db, report_id)


# TODO extension function should be replaced with simple extend which would take a db plugin
# it could look like that:
#   `db.extend(goodmap_db_plugin)` in plugin all those functions would be organized


def extend_db_with_goodmap_queries(db, location_model):
    db.extend("get_data", get_data(db))
    db.extend("get_visible_data", get_visible_data(db))
    db.extend("get_meta_data", get_meta_data(db))
    db.extend("get_locations", get_locations(db, location_model))
    db.extend("get_locations_paginated", get_locations_paginated(db, location_model))
    db.extend("get_location", get_location(db, location_model))
    db.extend("add_location", partial(add_location, location_model=location_model))
    db.extend("update_location", partial(update_location, location_model=location_model))
    db.extend("delete_location", delete_location)
    db.extend("get_categories", get_categories(db))
    db.extend("get_category_data", get_category_data(db))
    db.extend("add_suggestion", add_suggestion)
    db.extend("get_suggestions", get_suggestions(db))
    db.extend("get_suggestions_paginated", get_suggestions_paginated(db))
    db.extend("get_suggestion", get_suggestion(db))
    db.extend("update_suggestion", update_suggestion)
    db.extend("delete_suggestion", delete_suggestion)
    db.extend("add_report", add_report)
    db.extend("get_reports", get_reports(db))
    db.extend("get_reports_paginated", get_reports_paginated(db))
    db.extend("get_report", get_report(db))
    db.extend("update_report", update_report)
    db.extend("delete_report", delete_report)
    return db

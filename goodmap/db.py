import logging
from functools import partial
from types import SimpleNamespace
from typing import Any

from platzky.db.github_json_db import GithubJsonDb
from platzky.db.google_json_db import GoogleJsonDb
from platzky.db.json_db import Json
from platzky.db.json_file_db import JsonFile
from platzky.db.mongodb_db import MongoDB

from goodmap.core import get_queried_data
from goodmap.data_models.location import LocationBase
from goodmap.exceptions import (
    AlreadyExistsError,
    LocationAlreadyExistsError,
    LocationNotFoundError,
    ReportNotFoundError,
)

logger = logging.getLogger(__name__)

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


_UNSUPPORTED = "Goodmap does not support the {} database backend"


def _backend_prefix(db):
    """Return the prefix of the Goodmap query functions that serve this Platzky backend.

    Raises:
        NotImplementedError: If the backend has no Goodmap query functions.
    """
    # Most specific first: GoogleJsonDb, JsonFile and GithubJsonDb all subclass Json.
    if isinstance(db, MongoDB):
        return "mongodb_db"
    if isinstance(db, GoogleJsonDb):
        return "google_json_db"
    if isinstance(db, JsonFile):
        return "json_file_db"
    if isinstance(db, GithubJsonDb):
        raise NotImplementedError(_UNSUPPORTED.format(type(db).__name__))
    if isinstance(db, Json):
        return "json_db"
    raise NotImplementedError(_UNSUPPORTED.format(type(db).__name__))


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
        # Apply sorting. sorted(), not list.sort(): items may be the live JSON document's
        # list, which a read must never reorder.
        if sort_by:
            reverse = sort_order == "desc"
            items = sorted(
                items,
                key=lambda item: PaginationHelper.get_sort_key(item, sort_by),  # type: ignore[reportUnknownLambdaType]
                reverse=reverse,
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


class CRUDHelper:
    """Common CRUD operation utilities to eliminate duplication."""

    @staticmethod
    def add_item_to_json_db(db_data, collection_name, item_data, default_status=None):
        """Add item to JSON in-memory database."""
        collection = db_data.setdefault(collection_name, [])
        uuid = item_data.get("uuid")
        resource_type = collection_name.rstrip("s").capitalize()

        # Check if item already exists
        existing = next(
            (
                item
                for item in collection
                if (item.get("uuid") if isinstance(item, dict) else getattr(item, "uuid", None))
                == uuid
            ),
            None,
        )
        if existing:
            raise AlreadyExistsError(uuid, resource_type)

        record = dict(item_data)
        if default_status:
            record["status"] = default_status
        collection.append(record)

    @staticmethod
    def add_item_to_mongodb(db_collection, item_data, item_type, default_status=None):
        """Add item to MongoDB database."""
        existing = db_collection.find_one({"uuid": item_data.get("uuid")})
        if existing:
            raise AlreadyExistsError(item_data.get("uuid"), item_type)

        record = dict(item_data)
        if default_status:
            record["status"] = default_status
        db_collection.insert_one(record)


# ------------------------------------------------
# get_location_obligatory_fields


def json_db_get_location_obligatory_fields(db):
    """Return location obligatory fields from in-memory JSON database."""
    return db.document.data.get("location_obligatory_fields", [])


def json_file_db_get_location_obligatory_fields(db):
    """Return location obligatory fields from JSON file database."""
    return db.document.data["map"].get("location_obligatory_fields", [])


def google_json_db_get_location_obligatory_fields(db):
    """Return location obligatory fields from Google Cloud Storage JSON."""
    return db.document.data.get("map", {}).get("location_obligatory_fields", [])


def mongodb_db_get_location_obligatory_fields(db):
    """Return location obligatory fields from MongoDB."""
    config_doc = db.database.config.find_one({"_id": "map_config"})
    if config_doc and "location_obligatory_fields" in config_doc:
        return config_doc["location_obligatory_fields"]
    return []


def get_location_obligatory_fields(db):
    """Dispatch to the backend-specific get_location_obligatory_fields function."""
    return globals()[f"{_backend_prefix(db)}_get_location_obligatory_fields"](db)


# ------------------------------------------------
# get_issue_options


def json_db_get_issue_options(self):
    """Return reported issue types from in-memory JSON database."""
    return self.document.data.get("reported_issue_types", [])


def json_file_db_get_issue_options(self):
    """Return reported issue types from JSON file database."""
    return self.document.data["map"].get("reported_issue_types", [])


def google_json_db_get_issue_options(self):
    """Return reported issue types from Google Cloud Storage JSON."""
    return self.document.data.get("map", {}).get("reported_issue_types", [])


def mongodb_db_get_issue_options(self):
    """Return reported issue types from MongoDB."""
    config_doc = self.database.config.find_one({"_id": "map_config"})
    if config_doc and "reported_issue_types" in config_doc:
        return config_doc["reported_issue_types"]
    return []


def get_issue_options(db):
    """Dispatch to the backend-specific get_issue_options function."""
    return globals()[f"{_backend_prefix(db)}_get_issue_options"]


# ------------------------------------------------
# get_data


def google_json_db_get_data(self):
    """Return map data from Google Cloud Storage JSON."""
    return self.document.data.get("map", {})


def json_file_db_get_data(self):
    """Return map data from JSON file database."""
    return self.document.data["map"]


def json_db_get_data(self):
    """Return map data from in-memory JSON database."""
    return self.document.data


def mongodb_db_get_data(self):
    """Return map data from MongoDB, including locations and config."""
    config_doc = self.database.config.find_one({"_id": "map_config"})
    if config_doc:
        return {
            "data": list(self.database.locations.find({}, {"_id": 0})),
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
    """Dispatch to the backend-specific get_data function."""
    return globals()[f"{_backend_prefix(db)}_get_data"]


# ------------------------------------------------
# get_visible_data


def google_json_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from Google Cloud Storage JSON blob.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if not found.
    """
    return self.document.data.get("map", {}).get("visible_data", {})


def json_file_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from JSON file database.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if not found.
    """
    return self.document.data.get("map", {}).get("visible_data", {})


def json_db_get_visible_data(self) -> dict[str, Any]:
    """
    Retrieve visible data configuration from in-memory JSON database.

    Returns:
        dict: Dictionary containing field visibility configuration.
              Returns empty dict if not found.
    """
    return self.document.data.get("visible_data", {})


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
    config_doc = self.database.config.find_one({"_id": "map_config"})
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
    return globals()[f"{_backend_prefix(db)}_get_visible_data"]


# ------------------------------------------------
# get_meta_data


def google_json_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from Google Cloud Storage JSON blob.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if not found.
    """
    return self.document.data.get("map", {}).get("meta_data", {})


def json_file_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from JSON file database.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if not found.
    """
    return self.document.data.get("map", {}).get("meta_data", {})


def json_db_get_meta_data(self) -> dict[str, Any]:
    """
    Retrieve metadata configuration from in-memory JSON database.

    Returns:
        dict: Dictionary containing metadata configuration.
              Returns empty dict if not found.
    """
    return self.document.data.get("meta_data", {})


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
    config_doc = self.database.config.find_one({"_id": "map_config"})
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
    return globals()[f"{_backend_prefix(db)}_get_meta_data"]


# ------------------------------------------------
# get_marker_styles


def google_json_db_get_marker_styles(self) -> dict[str, Any]:
    """
    Retrieve marker icon/color styling configuration from Google Cloud Storage JSON blob.

    Returns:
        dict: Pin styling lookup table (icon_field, color_field, icons, colors).
              Returns empty dict if not found.
    """
    return self.document.data.get("map", {}).get("marker_styles", {})


def json_file_db_get_marker_styles(self) -> dict[str, Any]:
    """
    Retrieve marker icon/color styling configuration from JSON file database.

    Returns:
        dict: Pin styling lookup table (icon_field, color_field, icons, colors).
              Returns empty dict if not found.
    """
    return self.document.data.get("map", {}).get("marker_styles", {})


def json_db_get_marker_styles(self) -> dict[str, Any]:
    """
    Retrieve marker icon/color styling configuration from in-memory JSON database.

    Returns:
        dict: Pin styling lookup table (icon_field, color_field, icons, colors).
              Returns empty dict if not found.
    """
    return self.document.data.get("marker_styles", {})


def mongodb_db_get_marker_styles(self) -> dict[str, Any]:
    """
    Retrieve marker icon/color styling configuration from MongoDB.

    Returns:
        dict: Pin styling lookup table (icon_field, color_field, icons, colors).
              Returns empty dict if config document not found or field missing.
    """
    config_doc = self.database.config.find_one({"_id": "map_config"})
    if config_doc:
        return config_doc.get("marker_styles", {})
    return {}


def get_marker_styles(db):
    """
    Get the appropriate get_marker_styles function for the given database backend.

    Args:
        db: Database instance (must have module_name attribute).

    Returns:
        callable: Backend-specific get_marker_styles function.
    """
    return globals()[f"{_backend_prefix(db)}_get_marker_styles"]


# ------------------------------------------------
# get_initial_view


def google_json_db_get_initial_view(self) -> dict[str, Any]:
    """
    Retrieve the map's opening view from Google Cloud Storage JSON blob.

    Returns:
        dict: Raw ``initial_view`` config (center, zoom). Returns empty dict if
              not found - declaring a view is optional.
    """
    return self.document.data.get("map", {}).get("initial_view", {})


def json_file_db_get_initial_view(self) -> dict[str, Any]:
    """
    Retrieve the map's opening view from JSON file database.

    Returns:
        dict: Raw ``initial_view`` config (center, zoom). Returns empty dict if
              not found - declaring a view is optional.
    """
    return self.document.data.get("map", {}).get("initial_view", {})


def json_db_get_initial_view(self) -> dict[str, Any]:
    """
    Retrieve the map's opening view from in-memory JSON database.

    Returns:
        dict: Raw ``initial_view`` config (center, zoom). Returns empty dict if
              not found - declaring a view is optional.
    """
    return self.document.data.get("initial_view", {})


def mongodb_db_get_initial_view(self) -> dict[str, Any]:
    """
    Retrieve the map's opening view from MongoDB.

    Returns:
        dict: Raw ``initial_view`` config (center, zoom). Returns empty dict if
              the config document is missing or does not declare one.
    """
    config_doc = self.database.config.find_one({"_id": "map_config"})
    if config_doc:
        return config_doc.get("initial_view", {})
    return {}


def get_initial_view(db):
    """
    Get the appropriate get_initial_view function for the given database backend.

    Args:
        db: Database instance (must have module_name attribute).

    Returns:
        callable: Backend-specific get_initial_view function.
    """
    return globals()[f"{_backend_prefix(db)}_get_initial_view"]


# ------------------------------------------------
# get_categories


def json_db_get_categories(self):
    """Return category keys from in-memory JSON database."""
    return self.document.data.get("categories", {}).keys()


def json_file_db_get_categories(self):
    """Return category keys from JSON file database."""
    return self.document.data["map"].get("categories", {}).keys()


def google_json_db_get_categories(self):
    """Return category keys from Google Cloud Storage JSON."""
    return self.document.data.get("map", {}).get("categories", {}).keys()


def mongodb_db_get_categories(self):
    """Return category keys from MongoDB."""
    config_doc = self.database.config.find_one({"_id": "map_config"})
    if config_doc and "categories" in config_doc:
        return list(config_doc["categories"].keys())
    return []


def get_categories(db):
    """Dispatch to the backend-specific get_categories function."""
    return globals()[f"{_backend_prefix(db)}_get_categories"]


# ------------------------------------------------
# get_category_data


def json_db_get_category_data(self, category_type=None):
    """Return category data from in-memory JSON database, optionally filtered by type."""
    if category_type:
        return {
            "categories": {
                category_type: self.document.data.get("categories", {}).get(category_type, [])
            },
            "categories_help": self.document.data.get("categories_help", []),
            "categories_options_help": {
                category_type: self.document.data.get("categories_options_help", {}).get(
                    category_type, []
                )
            },
            "categories_default_checked": {
                category_type: self.document.data.get("categories_default_checked", {}).get(
                    category_type, []
                )
            },
            "categories_filter_mode": {
                category_type: self.document.data.get("categories_filter_mode", {}).get(
                    category_type, "or"
                )
            },
        }
    return {
        "categories": self.document.data.get("categories", {}),
        "categories_help": self.document.data.get("categories_help", []),
        "categories_options_help": self.document.data.get("categories_options_help", {}),
        "categories_default_checked": self.document.data.get("categories_default_checked", {}),
        "categories_filter_mode": self.document.data.get("categories_filter_mode", {}),
    }


def json_file_db_get_category_data(self, category_type=None):
    """Return category data from JSON file database, optionally filtered by type."""
    data = self.document.data["map"]
    if category_type:
        return {
            "categories": {category_type: data.get("categories", {}).get(category_type, [])},
            "categories_help": data.get("categories_help", []),
            "categories_options_help": {
                category_type: data.get("categories_options_help", {}).get(category_type, [])
            },
            "categories_default_checked": {
                category_type: data.get("categories_default_checked", {}).get(category_type, [])
            },
            "categories_filter_mode": {
                category_type: data.get("categories_filter_mode", {}).get(category_type, "or")
            },
        }
    return {
        "categories": data.get("categories", {}),
        "categories_help": data.get("categories_help", []),
        "categories_options_help": data.get("categories_options_help", {}),
        "categories_default_checked": data.get("categories_default_checked", {}),
        "categories_filter_mode": data.get("categories_filter_mode", {}),
    }


def google_json_db_get_category_data(self, category_type=None):
    """Return category data from Google Cloud Storage JSON, optionally filtered by type."""
    data = self.document.data.get("map", {})
    if category_type:
        return {
            "categories": {category_type: data.get("categories", {}).get(category_type, [])},
            "categories_help": data.get("categories_help", []),
            "categories_options_help": {
                category_type: data.get("categories_options_help", {}).get(category_type, [])
            },
            "categories_default_checked": {
                category_type: data.get("categories_default_checked", {}).get(category_type, [])
            },
            "categories_filter_mode": {
                category_type: data.get("categories_filter_mode", {}).get(category_type, "or")
            },
        }
    return {
        "categories": data.get("categories", {}),
        "categories_help": data.get("categories_help", []),
        "categories_options_help": data.get("categories_options_help", {}),
        "categories_default_checked": data.get("categories_default_checked", {}),
        "categories_filter_mode": data.get("categories_filter_mode", {}),
    }


def mongodb_db_get_category_data(self, category_type=None):
    """Return category data from MongoDB, optionally filtered by type."""
    config_doc = self.database.config.find_one({"_id": "map_config"})
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
                "categories_default_checked": {
                    category_type: config_doc.get("categories_default_checked", {}).get(
                        category_type, []
                    )
                },
                "categories_filter_mode": {
                    category_type: config_doc.get("categories_filter_mode", {}).get(
                        category_type, "or"
                    )
                },
            }
        return {
            "categories": config_doc.get("categories", {}),
            "categories_help": config_doc.get("categories_help", []),
            "categories_options_help": config_doc.get("categories_options_help", {}),
            "categories_default_checked": config_doc.get("categories_default_checked", {}),
            "categories_filter_mode": config_doc.get("categories_filter_mode", {}),
        }
    return {
        "categories": {},
        "categories_help": [],
        "categories_options_help": {},
        "categories_default_checked": {},
        "categories_filter_mode": {},
    }


def get_category_data(db):
    """Dispatch to the backend-specific get_category_data function."""
    return globals()[f"{_backend_prefix(db)}_get_category_data"]


# ------------------------------------------------
# get_location


def get_location_from_raw_data(raw_data, uuid, location_model):
    """Find and validate a single location by UUID from raw data.

    Args:
        raw_data: Dict containing a 'data' key with a list of location dicts.
        uuid: UUID string of the location to find.
        location_model: Pydantic model class to validate the location.

    Returns:
        Validated location model instance, or None if not found.
    """
    point = next((point for point in raw_data["data"] if point["uuid"] == uuid), None)
    return location_model.model_validate(point) if point else None


def google_json_db_get_location(self, uuid, location_model):
    """Retrieve a single location by UUID from Google Cloud Storage JSON."""
    return get_location_from_raw_data(self.document.data.get("map", {}), uuid, location_model)


def json_file_db_get_location(self, uuid, location_model):
    """Retrieve a single location by UUID from JSON file database."""
    return get_location_from_raw_data(self.document.data["map"], uuid, location_model)


def json_db_get_location(self, uuid, location_model):
    """Retrieve a single location by UUID from in-memory JSON database."""
    return get_location_from_raw_data(self.document.data, uuid, location_model)


def mongodb_db_get_location(self, uuid, location_model):
    """Retrieve a single location by UUID from MongoDB."""
    location_doc = self.database.locations.find_one({"uuid": uuid}, {"_id": 0})
    return location_model.model_validate(location_doc) if location_doc else None


def get_location(db, location_model):
    """Dispatch to the backend-specific get_location function."""
    return partial(globals()[f"{_backend_prefix(db)}_get_location"], location_model=location_model)


# ------------------------------------------------
# get_locations


def get_locations_list_from_raw_data(map_data, query, location_model):
    """Filter and validate locations from raw map data based on query parameters.

    Args:
        map_data: Dict containing a 'data' key, and optionally 'categories'.
        query: Dict of query parameters for filtering.
        location_model: Pydantic model class to validate each location.

    Returns:
        List of validated location model instances.
    """
    filtered_locations = get_queried_data(
        map_data["data"],
        map_data.get("categories", {}),
        query,
        map_data.get("categories_filter_mode", {}),
    )
    return [location_model.model_validate(point) for point in filtered_locations]


def google_json_db_get_locations(self, query, location_model):
    """Retrieve filtered locations from Google Cloud Storage JSON."""
    return get_locations_list_from_raw_data(
        self.document.data.get("map", {}), query, location_model
    )


def json_file_db_get_locations(self, query, location_model):
    """Retrieve filtered locations from JSON file database."""
    return get_locations_list_from_raw_data(self.document.data["map"], query, location_model)


def json_db_get_locations(self, query, location_model):
    """Retrieve filtered locations from in-memory JSON database."""
    return get_locations_list_from_raw_data(self.document.data, query, location_model)


def mongodb_db_get_locations(self, query, location_model):
    """Retrieve filtered locations from MongoDB."""
    config_doc = self.database.config.find_one({"_id": "map_config"}) or {}
    filter_modes = config_doc.get("categories_filter_mode", {})

    mongo_query = {}
    for key, values in query.items():
        if not values:
            continue
        mode = filter_modes.get(key, "or")
        if mode == "threshold":
            # Threshold categories (e.g. speed limits) are numeric and ordered:
            # selecting a value also matches any stored value at or below it.
            # Assumes the field is stored numerically in MongoDB.
            try:
                mongo_query[key] = {"$lte": max(float(value) for value in values)}
            except (TypeError, ValueError):
                # Match nothing for this category, same as goodmap.filtering's
                # _matches_threshold (which returns False on the same error),
                # rather than silently dropping the filter and matching everything.
                mongo_query[key] = {"$in": []}
        elif mode == "and":
            # Entry must have every selected value, not just any of them.
            mongo_query[key] = {"$all": values}
        else:
            # "or", "exclusive", and "boolean" all match any of the selected values.
            mongo_query[key] = {"$in": values}

    projection = {"_id": 0, "uuid": 1, "position": 1, "remark": 1}
    data = self.database.locations.find(mongo_query, projection)
    return (LocationBase.model_validate(loc) for loc in data)


def get_locations(db, location_model):
    """Dispatch to the backend-specific get_locations function."""
    return partial(globals()[f"{_backend_prefix(db)}_get_locations"], location_model=location_model)


def google_json_db_get_locations_paginated(self, query, location_model):
    """Google JSON locations with improved pagination."""
    # Get all locations from raw data
    data = self.document.data.get("map", {})
    all_locations = list(get_locations_list_from_raw_data(data, query, location_model))
    return PaginationHelper.create_paginated_response(all_locations, query)


def json_db_get_locations_paginated(self, query, location_model):
    """JSON locations with improved pagination."""
    # Get all locations from raw data
    all_locations = list(
        get_locations_list_from_raw_data(self.document.data, query, location_model)
    )
    return PaginationHelper.create_paginated_response(all_locations, query)


def json_file_db_get_locations_paginated(self, query, location_model):
    """JSON file locations with improved pagination."""
    data = self.document.data["map"]
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
    total_count = self.database.locations.count_documents(mongo_query)

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
    cursor = self.database.locations.aggregate(pipeline)
    locations = [location_model.model_validate(loc) for loc in cursor]

    # Convert items to dict if needed (for location models)
    if locations and hasattr(locations[0], "model_dump"):
        serialized_locations = [x.model_dump() for x in locations]
    else:
        serialized_locations = locations

    return __build_pagination_response(serialized_locations, total_count, page, per_page)


def get_locations_paginated(db, location_model):
    """Dispatch to the backend-specific get_locations_paginated function."""
    return partial(
        globals()[f"{_backend_prefix(db)}_get_locations_paginated"], location_model=location_model
    )


# ------------------------------------------------
# add_location


def json_file_db_add_location(self, location_data, location_model):
    """Add a new location to the JSON file database.

    Raises:
        LocationAlreadyExistsError: If a location with the same UUID already exists.
    """
    location = location_model.model_validate(location_data)
    with self.document.edit() as data:
        map_data = data["map"].setdefault("data", [])
        if any(point.get("uuid") == location_data["uuid"] for point in map_data):
            raise LocationAlreadyExistsError(location_data["uuid"])
        map_data.append(location.model_dump())


def json_db_add_location(self, location_data, location_model):
    """Add a new location to the in-memory JSON database.

    Raises:
        LocationAlreadyExistsError: If a location with the same UUID already exists.
    """
    location = location_model.model_validate(location_data)
    with self.document.edit() as data:
        if any(point.get("uuid") == location_data["uuid"] for point in data.get("data", [])):
            raise LocationAlreadyExistsError(location_data["uuid"])
        data["data"].append(location.model_dump())


def mongodb_db_add_location(self, location_data, location_model):
    """Add a new location to MongoDB.

    Raises:
        LocationAlreadyExistsError: If a location with the same UUID already exists.
    """
    location = location_model.model_validate(location_data)
    existing = self.database.locations.find_one({"uuid": location_data["uuid"]})
    if existing:
        raise LocationAlreadyExistsError(location_data["uuid"])
    self.database.locations.insert_one(location.model_dump())


def add_location(db, location_data, location_model):
    """Dispatch to the backend-specific add_location function."""
    return globals()[f"{_backend_prefix(db)}_add_location"](db, location_data, location_model)


# ------------------------------------------------
# update_location


def json_file_db_update_location(self, uuid, location_data, location_model):
    """Update an existing location in the JSON file database.

    Raises:
        LocationNotFoundError: If no location with the given UUID exists.
    """
    location = location_model.model_validate(location_data)
    with self.document.edit() as data:
        map_data = data["map"].get("data", [])
        idx = next((i for i, point in enumerate(map_data) if point.get("uuid") == uuid), None)
        if idx is None:
            raise LocationNotFoundError(uuid)
        map_data[idx] = location.model_dump()


def json_db_update_location(self, uuid, location_data, location_model):
    """Update an existing location in the in-memory JSON database.

    Raises:
        LocationNotFoundError: If no location with the given UUID exists.
    """
    location = location_model.model_validate(location_data)
    with self.document.edit() as data:
        map_data = data.get("data", [])
        idx = next((i for i, point in enumerate(map_data) if point.get("uuid") == uuid), None)
        if idx is None:
            raise LocationNotFoundError(uuid)
        map_data[idx] = location.model_dump()


def mongodb_db_update_location(self, uuid, location_data, location_model):
    """Update an existing location in MongoDB.

    Raises:
        LocationNotFoundError: If no location with the given UUID exists.
    """
    location = location_model.model_validate(location_data)
    result = self.database.locations.update_one({"uuid": uuid}, {"$set": location.model_dump()})
    if result.matched_count == 0:
        raise LocationNotFoundError(uuid)


def update_location(db, uuid, location_data, location_model):
    """Dispatch to the backend-specific update_location function."""
    return globals()[f"{_backend_prefix(db)}_update_location"](
        db, uuid, location_data, location_model
    )


# ------------------------------------------------
# delete_location


def json_file_db_delete_location(self, uuid):
    """Delete a location from the JSON file database.

    Raises:
        LocationNotFoundError: If no location with the given UUID exists.
    """
    with self.document.edit() as data:
        map_data = data["map"].get("data", [])
        idx = next((i for i, point in enumerate(map_data) if point.get("uuid") == uuid), None)
        if idx is None:
            raise LocationNotFoundError(uuid)
        del map_data[idx]


def json_db_delete_location(self, uuid):
    """Delete a location from the in-memory JSON database.

    Raises:
        LocationNotFoundError: If no location with the given UUID exists.
    """
    with self.document.edit() as data:
        map_data = data.get("data", [])
        idx = next((i for i, point in enumerate(map_data) if point.get("uuid") == uuid), None)
        if idx is None:
            raise LocationNotFoundError(uuid)
        del map_data[idx]


def mongodb_db_delete_location(self, uuid):
    """Delete a location from MongoDB.

    Raises:
        LocationNotFoundError: If no location with the given UUID exists.
    """
    result = self.database.locations.delete_one({"uuid": uuid})
    if result.deleted_count == 0:
        raise LocationNotFoundError(uuid)


def delete_location(db, uuid):
    """Dispatch to the backend-specific delete_location function."""
    return globals()[f"{_backend_prefix(db)}_delete_location"](db, uuid)


# ------------------------------------------------
# add_suggestion


def json_db_add_suggestion(self, suggestion_data):
    """Add a suggestion to the in-memory JSON database with 'pending' status."""
    with self.document.edit() as data:
        CRUDHelper.add_item_to_json_db(data, "suggestions", suggestion_data, "pending")


def json_file_db_add_suggestion(self, suggestion_data):
    """Add a suggestion to the JSON file database with 'pending' status."""
    with self.document.edit() as data:
        CRUDHelper.add_item_to_json_db(data["map"], "suggestions", suggestion_data, "pending")


def mongodb_db_add_suggestion(self, suggestion_data):
    """Add a suggestion to MongoDB with 'pending' status."""
    CRUDHelper.add_item_to_mongodb(
        self.database.suggestions, suggestion_data, "Suggestion", "pending"
    )


def google_json_db_add_suggestion(self, suggestion_data):
    """No-op for Google Cloud Storage JSON (read-only backend)."""
    # Temporary workaround: just use notifier without storing
    # Full implementation would require writing back to Google Cloud Storage
    pass


def add_suggestion(db, suggestion_data):
    """Dispatch to the backend-specific add_suggestion function."""
    return globals()[f"{_backend_prefix(db)}_add_suggestion"](db, suggestion_data)


# ------------------------------------------------
# get_suggestions


def json_db_get_suggestions(self, query_params):
    """Return suggestions from in-memory JSON database, optionally filtered by status."""
    suggestions = self.document.data.get("suggestions", [])

    statuses = query_params.get("status")
    if statuses:
        suggestions = [s for s in suggestions if s.get("status") in statuses]

    return suggestions


def json_db_get_suggestions_paginated(self, query):
    """JSON suggestions with improved pagination."""
    suggestions = self.document.data.get("suggestions", [])
    return PaginationHelper.create_paginated_response(suggestions, query)


def json_file_db_get_suggestions(self, query_params):
    """Return suggestions from JSON file database, optionally filtered by status."""
    suggestions = self.document.data["map"].get("suggestions", [])

    statuses = query_params.get("status")
    if statuses:
        suggestions = [s for s in suggestions if s.get("status") in statuses]

    return suggestions


def json_file_db_get_suggestions_paginated(self, query):
    """JSON file suggestions with improved pagination."""
    suggestions = self.document.data["map"].get("suggestions", [])
    return PaginationHelper.create_paginated_response(suggestions, query)


def mongodb_db_get_suggestions(self, query_params):
    """Return suggestions from MongoDB, optionally filtered by status."""
    query = {}
    statuses = query_params.get("status")
    if statuses:
        query["status"] = {"$in": statuses}

    return list(self.database.suggestions.find(query, {"_id": 0}))


def mongodb_db_get_suggestions_paginated(self, query):
    """MongoDB suggestions with improved pagination."""
    page, per_page, sort_by, sort_order = __parse_pagination_params(query)

    # Build MongoDB query
    mongo_query = {}
    statuses = query.get("status")
    if statuses:
        mongo_query["status"] = {"$in": statuses}

    # Get total count
    total_count = self.database.suggestions.count_documents(mongo_query)

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
    cursor = self.database.suggestions.aggregate(pipeline)
    items = list(cursor)

    return __build_pagination_response(items, total_count, page, per_page)


def google_json_db_get_suggestions(self, query_params):
    """Return empty list for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, suggestions not stored in blob
    return []


def google_json_db_get_suggestions_paginated(self, query):
    """Google JSON suggestions with pagination (read-only)."""
    return PaginationHelper.create_paginated_response([], query)


def get_suggestions(db):
    """Dispatch to the backend-specific get_suggestions function."""
    return globals()[f"{_backend_prefix(db)}_get_suggestions"]


def get_suggestions_paginated(db):
    """Dispatch to the backend-specific get_suggestions_paginated function."""
    return globals()[f"{_backend_prefix(db)}_get_suggestions_paginated"]


# ------------------------------------------------
# get_suggestion


def json_db_get_suggestion(self, suggestion_id):
    """Return a single suggestion by UUID from in-memory JSON database."""
    return next(
        (s for s in self.document.data.get("suggestions", []) if s.get("uuid") == suggestion_id),
        None,
    )


def json_file_db_get_suggestion(self, suggestion_id):
    """Return a single suggestion by UUID from JSON file database."""
    return next(
        (
            s
            for s in self.document.data["map"].get("suggestions", [])
            if s.get("uuid") == suggestion_id
        ),
        None,
    )


def mongodb_db_get_suggestion(self, suggestion_id):
    """Return a single suggestion by UUID from MongoDB."""
    return self.database.suggestions.find_one({"uuid": suggestion_id}, {"_id": 0})


def google_json_db_get_suggestion(self, suggestion_id):
    """Return None for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, suggestions not stored in blob
    return None


def get_suggestion(db):
    """Dispatch to the backend-specific get_suggestion function."""
    return globals()[f"{_backend_prefix(db)}_get_suggestion"]


# ------------------------------------------------
# update_suggestion


def json_db_update_suggestion(self, suggestion_id, status):
    """Update a suggestion's status in the in-memory JSON database.

    Raises:
        ValueError: If no suggestion with the given UUID exists.
    """
    with self.document.edit() as data:
        for s in data.get("suggestions", []):
            if s.get("uuid") == suggestion_id:
                s["status"] = status
                return
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def json_file_db_update_suggestion(self, suggestion_id, status):
    """Update a suggestion's status in the JSON file database.

    Raises:
        ValueError: If no suggestion with the given UUID exists.
    """
    with self.document.edit() as data:
        for s in data["map"].get("suggestions", []):
            if s.get("uuid") == suggestion_id:
                s["status"] = status
                return
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def mongodb_db_update_suggestion(self, suggestion_id, status):
    """Update a suggestion's status in MongoDB.

    Raises:
        ValueError: If no suggestion with the given UUID exists.
    """
    result = self.database.suggestions.update_one(
        {"uuid": suggestion_id}, {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def google_json_db_update_suggestion(self, suggestion_id, status):
    """No-op for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, no-op
    pass


def update_suggestion(db, suggestion_id, status):
    """Dispatch to the backend-specific update_suggestion function."""
    return globals()[f"{_backend_prefix(db)}_update_suggestion"](db, suggestion_id, status)


# ------------------------------------------------
# delete_suggestion


def json_db_delete_suggestion(self, suggestion_id):
    """Delete a suggestion from the in-memory JSON database.

    Raises:
        ValueError: If no suggestion with the given UUID exists.
    """
    with self.document.edit() as data:
        suggestions = data.get("suggestions", [])
        idx = next((i for i, s in enumerate(suggestions) if s.get("uuid") == suggestion_id), None)
        if idx is None:
            raise ValueError(f"Suggestion with uuid {suggestion_id} not found")
        del suggestions[idx]


def json_file_db_delete_suggestion(self, suggestion_id):
    """Delete a suggestion from the JSON file database.

    Raises:
        ValueError: If no suggestion with the given UUID exists.
    """
    with self.document.edit() as data:
        suggestions = data["map"].get("suggestions", [])
        idx = next((i for i, s in enumerate(suggestions) if s.get("uuid") == suggestion_id), None)
        if idx is None:
            raise ValueError(f"Suggestion with uuid {suggestion_id} not found")
        del suggestions[idx]


def mongodb_db_delete_suggestion(self, suggestion_id):
    """Delete a suggestion from MongoDB.

    Raises:
        ValueError: If no suggestion with the given UUID exists.
    """
    result = self.database.suggestions.delete_one({"uuid": suggestion_id})
    if result.deleted_count == 0:
        raise ValueError(f"Suggestion with uuid {suggestion_id} not found")


def google_json_db_delete_suggestion(self, suggestion_id):
    """No-op for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, no-op
    pass


def delete_suggestion(db, suggestion_id):
    """Dispatch to the backend-specific delete_suggestion function."""
    return globals()[f"{_backend_prefix(db)}_delete_suggestion"](db, suggestion_id)


# ------------------------------------------------
# add_report


def json_db_add_report(self, report_data):
    """Add a report to the in-memory JSON database.

    Raises:
        ValueError: If a report with the same UUID already exists.
    """
    with self.document.edit() as data:
        reports = data.setdefault("reports", [])
        if any(r.get("uuid") == report_data.get("uuid") for r in reports):
            raise ValueError(f"Report with uuid {report_data['uuid']} already exists")
        reports.append(report_data)


def json_file_db_add_report(self, report_data):
    """Add a report to the JSON file database.

    Raises:
        ValueError: If a report with the same UUID already exists.
    """
    with self.document.edit() as data:
        reports = data["map"].setdefault("reports", [])
        if any(r.get("uuid") == report_data.get("uuid") for r in reports):
            raise ValueError(f"Report with uuid {report_data['uuid']} already exists")
        reports.append(report_data)


def mongodb_db_add_report(self, report_data):
    """Add a report to MongoDB.

    Raises:
        ValueError: If a report with the same UUID already exists.
    """
    existing = self.database.reports.find_one({"uuid": report_data.get("uuid")})
    if existing:
        raise ValueError(f"Report with uuid {report_data['uuid']} already exists")

    self.database.reports.insert_one(report_data)


def google_json_db_add_report(self, report_data):
    """No-op for Google Cloud Storage JSON (read-only backend)."""
    # Temporary workaround: just use notifier without storing
    # Full implementation would require writing back to Google Cloud Storage
    pass


def add_report(db, report_data):
    """Dispatch to the backend-specific add_report function."""
    return globals()[f"{_backend_prefix(db)}_add_report"](db, report_data)


# ------------------------------------------------
# get_reports


def json_db_get_reports(self, query_params):
    """Return reports from in-memory JSON database, optionally filtered by status and priority."""
    reports = self.document.data.get("reports", [])

    statuses = query_params.get("status")
    if statuses:
        reports = [r for r in reports if r.get("status") in statuses]

    priorities = query_params.get("priority")
    if priorities:
        reports = [r for r in reports if r.get("priority") in priorities]

    return reports


def json_db_get_reports_paginated(self, query):
    """JSON reports with improved pagination."""
    reports = self.document.data.get("reports", [])
    return PaginationHelper.create_paginated_response(reports, query)


def json_file_db_get_reports(self, query_params):
    """Return reports from JSON file database, optionally filtered by status and priority."""
    reports = self.document.data["map"].get("reports", [])

    statuses = query_params.get("status")
    if statuses:
        reports = [r for r in reports if r.get("status") in statuses]

    priorities = query_params.get("priority")
    if priorities:
        reports = [r for r in reports if r.get("priority") in priorities]

    return reports


def json_file_db_get_reports_paginated(self, query):
    """JSON file reports with improved pagination."""
    data = self.document.data["map"]
    reports = data.get("reports", [])
    return PaginationHelper.create_paginated_response(reports, query)


def mongodb_db_get_reports(self, query_params):
    """Return reports from MongoDB, optionally filtered by status and priority."""
    query = {}

    statuses = query_params.get("status")
    if statuses:
        query["status"] = {"$in": statuses}

    priorities = query_params.get("priority")
    if priorities:
        query["priority"] = {"$in": priorities}

    return list(self.database.reports.find(query, {"_id": 0}))


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
    total_count = self.database.reports.count_documents(mongo_query)

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
    cursor = self.database.reports.aggregate(pipeline)
    items = list(cursor)

    return __build_pagination_response(items, total_count, page, per_page)


def google_json_db_get_reports(self, query_params):
    """Return empty list for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, reports not stored in blob
    return []


def google_json_db_get_reports_paginated(self, query):
    """Google JSON reports with pagination (read-only)."""
    return PaginationHelper.create_paginated_response([], query)


def get_reports(db):
    """Dispatch to the backend-specific get_reports function."""
    return globals()[f"{_backend_prefix(db)}_get_reports"]


def get_reports_paginated(db):
    """Dispatch to the backend-specific get_reports_paginated function."""
    return globals()[f"{_backend_prefix(db)}_get_reports_paginated"]


# ------------------------------------------------
# get_report


def json_db_get_report(self, report_id):
    """Return a single report by UUID from in-memory JSON database."""
    return next(
        (r for r in self.document.data.get("reports", []) if r.get("uuid") == report_id), None
    )


def json_file_db_get_report(self, report_id):
    """Return a single report by UUID from JSON file database."""
    return next(
        (r for r in self.document.data["map"].get("reports", []) if r.get("uuid") == report_id),
        None,
    )


def mongodb_db_get_report(self, report_id):
    """Return a single report by UUID from MongoDB."""
    return self.database.reports.find_one({"uuid": report_id}, {"_id": 0})


def google_json_db_get_report(self, report_id):
    """Return None for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, reports not stored in blob
    return None


def get_report(db):
    """Dispatch to the backend-specific get_report function."""
    return globals()[f"{_backend_prefix(db)}_get_report"]


# ------------------------------------------------
# update_report


def json_db_update_report(self, report_id, status=None, priority=None):
    """Update a report's status and/or priority in the in-memory JSON database.

    Raises:
        ReportNotFoundError: If no report with the given UUID exists.
    """
    with self.document.edit() as data:
        for r in data.get("reports", []):
            if r.get("uuid") == report_id:
                if status:
                    r["status"] = status
                if priority:
                    r["priority"] = priority
                return
        raise ReportNotFoundError(report_id)


def json_file_db_update_report(self, report_id, status=None, priority=None):
    """Update a report's status and/or priority in the JSON file database.

    Raises:
        ReportNotFoundError: If no report with the given UUID exists.
    """
    with self.document.edit() as data:
        for r in data["map"].get("reports", []):
            if r.get("uuid") == report_id:
                if status:
                    r["status"] = status
                if priority:
                    r["priority"] = priority
                return
        raise ReportNotFoundError(report_id)


def mongodb_db_update_report(self, report_id, status=None, priority=None):
    """Update a report's status and/or priority in MongoDB.

    Raises:
        ReportNotFoundError: If no report with the given UUID exists.
    """
    update_doc = {}
    if status:
        update_doc["status"] = status
    if priority:
        update_doc["priority"] = priority

    if update_doc:
        result = self.database.reports.update_one({"uuid": report_id}, {"$set": update_doc})
        if result.matched_count == 0:
            raise ReportNotFoundError(report_id)


def google_json_db_update_report(self, report_id, status=None, priority=None):
    """No-op for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, no-op
    pass


def update_report(db, report_id, status=None, priority=None):
    """Dispatch to the backend-specific update_report function."""
    return globals()[f"{_backend_prefix(db)}_update_report"](db, report_id, status, priority)


# ------------------------------------------------
# delete_report


def json_db_delete_report(self, report_id):
    """Delete a report from the in-memory JSON database.

    Raises:
        ReportNotFoundError: If no report with the given UUID exists.
    """
    with self.document.edit() as data:
        reports = data.get("reports", [])
        idx = next((i for i, r in enumerate(reports) if r.get("uuid") == report_id), None)
        if idx is None:
            raise ReportNotFoundError(report_id)
        del reports[idx]


def json_file_db_delete_report(self, report_id):
    """Delete a report from the JSON file database.

    Raises:
        ReportNotFoundError: If no report with the given UUID exists.
    """
    with self.document.edit() as data:
        reports = data["map"].get("reports", [])
        idx = next((i for i, r in enumerate(reports) if r.get("uuid") == report_id), None)
        if idx is None:
            raise ReportNotFoundError(report_id)
        del reports[idx]


def mongodb_db_delete_report(self, report_id):
    """Delete a report from MongoDB.

    Raises:
        ReportNotFoundError: If no report with the given UUID exists.
    """
    result = self.database.reports.delete_one({"uuid": report_id})
    if result.deleted_count == 0:
        raise ReportNotFoundError(report_id)


def google_json_db_delete_report(self, report_id):
    """No-op for Google Cloud Storage JSON (read-only backend)."""
    # GoogleJsonDb is read-only, no-op
    pass


def delete_report(db, report_id):
    """Dispatch to the backend-specific delete_report function."""
    return globals()[f"{_backend_prefix(db)}_delete_report"](db, report_id)


def goodmap_queries(db, location_model):
    """Collect the Goodmap query functions for the database backend.

    Binds the backend-specific implementations of all CRUD operations for
    locations, suggestions, and reports to the given database. The database
    itself is left untouched.

    Args:
        db: Platzky database instance the queries run against.
        location_model: Pydantic model class used for location validation.

    Returns:
        A namespace whose attributes (``get_data``, ``add_location``, ...) are
        the query functions, each with ``db`` already bound.
    """
    queries = {
        "get_issue_options": get_issue_options(db),
        "get_data": get_data(db),
        "get_marker_styles": get_marker_styles(db),
        "get_initial_view": get_initial_view(db),
        "get_locations": get_locations(db, location_model),
        "get_locations_paginated": get_locations_paginated(db, location_model),
        "get_location": get_location(db, location_model),
        "add_location": partial(add_location, location_model=location_model),
        "update_location": partial(update_location, location_model=location_model),
        "delete_location": delete_location,
        "get_categories": get_categories(db),
        "get_category_data": get_category_data(db),
        "add_suggestion": add_suggestion,
        "get_suggestions": get_suggestions(db),
        "get_suggestions_paginated": get_suggestions_paginated(db),
        "get_suggestion": get_suggestion(db),
        "update_suggestion": update_suggestion,
        "delete_suggestion": delete_suggestion,
        "add_report": add_report,
        "get_reports": get_reports(db),
        "get_reports_paginated": get_reports_paginated(db),
        "get_report": get_report(db),
        "update_report": update_report,
        "delete_report": delete_report,
    }
    return SimpleNamespace(**{name: partial(fn, db) for name, fn in queries.items()})

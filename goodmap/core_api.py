import importlib.metadata
import logging
import uuid

import numpy
import pysupercluster
from flask import Blueprint, jsonify, make_response, request
from flask_babel import gettext
from flask_restx import Api, Resource, fields
from platzky.config import LanguagesMapping
from werkzeug.exceptions import BadRequest

from goodmap.clustering import (
    map_clustering_data_to_proper_lazy_loading_object,
    match_clusters_uuids,
)
from goodmap.exceptions import (
    LocationAlreadyExistsError,
    LocationNotFoundError,
    LocationValidationError,
    ReportNotFoundError,
)
from goodmap.formatter import prepare_pin

# SuperCluster configuration constants
MIN_ZOOM = 0
MAX_ZOOM = 16
CLUSTER_RADIUS = 200
CLUSTER_EXTENT = 512

# Error message constants
ERROR_INVALID_REQUEST_DATA = "Invalid request data"
ERROR_INVALID_LOCATION_DATA = "Invalid location data"
ERROR_INTERNAL_ERROR = "An internal error occurred"

logger = logging.getLogger(__name__)


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def get_or_none(data, *keys):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


def get_locations_from_request(database, request_args, as_basic_info=False):
    """
    Shared helper to fetch locations from database based on request arguments.

    Args:
        database: Database instance
        request_args: Request arguments (flask.request.args)
        as_basic_info: If True, returns list of basic_info dicts, otherwise returns Location objects

    Returns:
        List of locations (either as objects or basic_info dicts)
    """
    query_params = request_args.to_dict(flat=False)
    all_locations = database.get_locations(query_params)

    if as_basic_info:
        return [x.basic_info() for x in all_locations]

    return all_locations


def core_pages(
    database,
    languages: LanguagesMapping,
    notifier_function,
    csrf_generator,
    location_model,
    feature_flags={},
) -> Blueprint:
    core_api_blueprint = Blueprint("api", __name__, url_prefix="/api")
    core_api = Api(core_api_blueprint, doc="/doc", version="0.1")

    location_report_model = core_api.model(
        "LocationReport",
        {
            "id": fields.String(required=True, description="Location ID"),
            "description": fields.String(required=True, description="Description of the problem"),
        },
    )

    # TODO get this from Location pydantic model
    suggested_location_model = core_api.model(
        "LocationSuggestion",
        {
            "name": fields.String(required=False, description="Organization name"),
            "position": fields.String(required=True, description="Location of the suggestion"),
            "photo": fields.String(required=False, description="Photo of the location"),
        },
    )

    @core_api.route("/suggest-new-point")
    class NewLocation(Resource):
        @core_api.expect(suggested_location_model)
        def post(self):
            """Suggest new location"""
            try:
                suggested_location = request.get_json()
                suggested_location.update({"uuid": str(uuid.uuid4())})
                location = location_model.model_validate(suggested_location)
                database.add_suggestion(location.model_dump())
                message = (
                    f"A new location has been suggested under uuid: '{location.uuid}' "
                    f"at position: {location.position}"
                )
                notifier_function(message)
            except BadRequest:
                logger.warning("Invalid JSON in suggest endpoint")
                return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
            except LocationValidationError as e:
                logger.warning(
                    "Location validation failed in suggest endpoint",
                    extra={"errors": e.validation_errors},
                )
                return make_response(jsonify({"message": ERROR_INVALID_LOCATION_DATA}), 400)
            except Exception:
                logger.error("Error in suggest location endpoint", exc_info=True)
                return make_response(
                    jsonify({"message": "An error occurred while processing your suggestion"}), 500
                )
            return make_response(jsonify({"message": "Location suggested"}), 200)

    @core_api.route("/report-location")
    class ReportLocation(Resource):
        @core_api.expect(location_report_model)
        def post(self):
            """Report location"""
            try:
                location_report = request.get_json()
                report = {
                    "uuid": str(uuid.uuid4()),
                    "location_id": location_report["id"],
                    "description": location_report["description"],
                    "status": "pending",
                    "priority": "medium",
                }
                database.add_report(report)
                message = (
                    f"A location has been reported: '{location_report['id']}' "
                    f"with problem: {location_report['description']}"
                )
                notifier_function(message)
            except BadRequest:
                logger.warning("Invalid JSON in report location endpoint")
                return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
            except KeyError as e:
                logger.warning(
                    "Missing required field in report location", extra={"missing_field": str(e)}
                )
                error_message = gettext("Error reporting location")
                return make_response(jsonify({"message": error_message}), 400)
            except Exception:
                logger.error("Error in report location endpoint", exc_info=True)
                error_message = gettext("Error sending notification")
                return make_response(jsonify({"message": error_message}), 500)
            return make_response(jsonify({"message": gettext("Location reported")}), 200)

    @core_api.route("/locations")
    class GetLocations(Resource):
        def get(self):
            """
            Shows list of locations with uuid and position
            """
            locations = get_locations_from_request(database, request.args, as_basic_info=True)
            return jsonify(locations)

    @core_api.route("/locations-clustered")
    class GetLocationsClustered(Resource):
        def get(self):
            """
            Shows list of locations with uuid, position and clusters
            """
            try:
                query_params = request.args.to_dict(flat=False)
                zoom = int(query_params.get("zoom", [7])[0])

                # Validate zoom level (aligned with SuperCluster min_zoom/max_zoom)
                if not MIN_ZOOM <= zoom <= MAX_ZOOM:
                    return make_response(
                        jsonify({"message": f"Zoom must be between {MIN_ZOOM} and {MAX_ZOOM}"}),
                        400,
                    )

                points = get_locations_from_request(database, request.args, as_basic_info=True)
                if not points:
                    return jsonify([])

                points_numpy = numpy.array(
                    [(point["position"][0], point["position"][1]) for point in points]
                )

                index = pysupercluster.SuperCluster(
                    points_numpy,
                    min_zoom=MIN_ZOOM,
                    max_zoom=MAX_ZOOM,
                    radius=CLUSTER_RADIUS,
                    extent=CLUSTER_EXTENT,
                )

                clusters = index.getClusters(
                    top_left=(-180.0, 90.0),
                    bottom_right=(180.0, -90.0),
                    zoom=zoom,
                )
                clusters = match_clusters_uuids(points, clusters)

                return jsonify(map_clustering_data_to_proper_lazy_loading_object(clusters))
            except ValueError as e:
                logger.warning("Invalid parameter in clustering request: %s", e)
                return make_response(jsonify({"message": "Invalid parameters provided"}), 400)
            except Exception as e:
                logger.error("Clustering operation failed: %s", e, exc_info=True)
                return make_response(
                    jsonify({"message": "An error occurred during clustering"}), 500
                )

    @core_api.route("/location/<location_id>")
    class GetLocation(Resource):
        def get(self, location_id):
            """
            Shows a single location with all data
            """
            location = database.get_location(location_id)
            visible_data = database.get_visible_data()
            meta_data = database.get_meta_data()

            formatted_data = prepare_pin(location.model_dump(), visible_data, meta_data)
            return jsonify(formatted_data)

    @core_api.route("/version")
    class Version(Resource):
        def get(self):
            """Shows backend version"""
            version_info = {"backend": importlib.metadata.version("goodmap")}
            return jsonify(version_info)

    @core_api.route("/categories")
    class Categories(Resource):
        def get(self):
            """Shows all available categories"""
            raw_categories = database.get_categories()
            categories = make_tuple_translation(raw_categories)

            if not feature_flags.get("CATEGORIES_HELP", False):
                return jsonify(categories)
            else:
                category_data = database.get_category_data()
                categories_help = category_data["categories_help"]
                proper_categories_help = []
                if categories_help is not None:
                    for option in categories_help:
                        proper_categories_help.append(
                            {option: gettext(f"categories_help_{option}")}
                        )

            return jsonify({"categories": categories, "categories_help": proper_categories_help})

    @core_api.route("/languages")
    class Languages(Resource):
        def get(self):
            """Shows all available languages"""
            return jsonify(languages)

    @core_api.route("/category/<category_type>")
    class CategoryTypes(Resource):
        def get(self, category_type):
            """Shows all available types in category"""
            category_data = database.get_category_data(category_type)
            local_data = make_tuple_translation(category_data["categories"][category_type])

            categories_options_help = get_or_none(
                category_data, "categories_options_help", category_type
            )
            proper_categories_options_help = []
            if categories_options_help is not None:
                for option in categories_options_help:
                    proper_categories_options_help.append(
                        {option: gettext(f"categories_options_help_{option}")}
                    )
            if not feature_flags.get("CATEGORIES_HELP", False):
                return jsonify(local_data)
            else:
                return jsonify(
                    {
                        "categories_options": local_data,
                        "categories_options_help": proper_categories_options_help,
                    }
                )

    @core_api.route("/generate-csrf-token")
    class CsrfToken(Resource):
        def get(self):
            csrf_token = csrf_generator()
            return {"csrf_token": csrf_token}

    @core_api.route("/admin/locations")
    class AdminManageLocations(Resource):
        def get(self):
            """
            Shows full list of locations, with optional server-side pagination, sorting,
            and filtering.
            """
            query_params = request.args.to_dict(flat=False)
            if "sort_by" not in query_params:
                query_params["sort_by"] = ["name"]
            result = database.get_locations_paginated(query_params)
            return jsonify(result)

        def post(self):
            """
            Creates a new location
            """
            location_data = request.get_json()
            try:
                location_data.update({"uuid": str(uuid.uuid4())})
                location = location_model.model_validate(location_data)
                database.add_location(location.model_dump())
            except LocationValidationError as e:
                logger.warning(
                    "Location validation failed",
                    extra={"uuid": e.uuid, "errors": e.validation_errors},
                )
                return make_response(jsonify({"message": ERROR_INVALID_LOCATION_DATA}), 400)
            except Exception:
                logger.error("Error creating location", exc_info=True)
                return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
            return jsonify(location.model_dump())

    @core_api.route("/admin/locations/<location_id>")
    class AdminManageLocation(Resource):
        def put(self, location_id):
            """
            Updates a single location
            """
            location_data = request.get_json()
            try:
                location_data.update({"uuid": location_id})
                location = location_model.model_validate(location_data)
                database.update_location(location_id, location.model_dump())
            except LocationValidationError as e:
                logger.warning(
                    "Location validation failed",
                    extra={"uuid": e.uuid, "errors": e.validation_errors},
                )
                return make_response(jsonify({"message": ERROR_INVALID_LOCATION_DATA}), 400)
            except LocationNotFoundError as e:
                logger.info("Location not found for update", extra={"uuid": e.uuid})
                return make_response(jsonify({"message": "Location not found"}), 404)
            except Exception:
                logger.error("Error updating location", exc_info=True)
                return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
            return jsonify(location.model_dump())

        def delete(self, location_id):
            """
            Deletes a single location
            """
            try:
                database.delete_location(location_id)
            except LocationNotFoundError as e:
                logger.info("Location not found for deletion", extra={"uuid": e.uuid})
                return make_response(jsonify({"message": "Location not found"}), 404)
            except Exception:
                logger.error("Error deleting location", exc_info=True)
                return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
            return "", 204

    @core_api.route("/admin/suggestions")
    class AdminManageSuggestions(Resource):
        def get(self):
            """
            List location suggestions, with optional server-side pagination, sorting,
            and filtering by status.
            """
            query_params = request.args.to_dict(flat=False)
            result = database.get_suggestions_paginated(query_params)
            return jsonify(result)

    @core_api.route("/admin/suggestions/<suggestion_id>")
    class AdminManageSuggestion(Resource):
        def put(self, suggestion_id):
            """
            Accept or reject a location suggestion
            """
            try:
                data = request.get_json()
                status = data.get("status")
                if status not in ("accepted", "rejected"):
                    return make_response(jsonify({"message": "Invalid status"}), 400)
                suggestion = database.get_suggestion(suggestion_id)
                if not suggestion:
                    return make_response(jsonify({"message": "Suggestion not found"}), 404)
                if suggestion.get("status") != "pending":
                    return make_response(jsonify({"message": "Suggestion already processed"}), 400)
                if status == "accepted":
                    suggestion_data = {k: v for k, v in suggestion.items() if k != "status"}
                    database.add_location(suggestion_data)
                database.update_suggestion(suggestion_id, status)
            except LocationValidationError as e:
                logger.warning(
                    "Location validation failed in suggestion",
                    extra={"uuid": e.uuid, "errors": e.validation_errors},
                )
                return make_response(jsonify({"message": ERROR_INVALID_LOCATION_DATA}), 400)
            except LocationAlreadyExistsError as e:
                logger.warning(
                    "Attempted to create duplicate location from suggestion", extra={"uuid": e.uuid}
                )
                return make_response(jsonify({"message": "Location already exists"}), 409)
            except Exception:
                logger.error("Error processing suggestion", exc_info=True)
                return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
            return jsonify(database.get_suggestion(suggestion_id))

    @core_api.route("/admin/reports")
    class AdminManageReports(Resource):
        def get(self):
            """
            List location reports, with optional server-side pagination, sorting,
            and filtering by status/priority.
            """
            query_params = request.args.to_dict(flat=False)
            result = database.get_reports_paginated(query_params)
            return jsonify(result)

    @core_api.route("/admin/reports/<report_id>")
    class AdminManageReport(Resource):
        def put(self, report_id):
            """
            Update a report's status and/or priority
            """
            try:
                data = request.get_json()
                status = data.get("status")
                priority = data.get("priority")
                valid_status = ("resolved", "rejected")
                valid_priority = ("critical", "high", "medium", "low")
                if status and status not in valid_status:
                    return make_response(jsonify({"message": "Invalid status"}), 400)
                if priority and priority not in valid_priority:
                    return make_response(jsonify({"message": "Invalid priority"}), 400)
                report = database.get_report(report_id)
                if not report:
                    return make_response(jsonify({"message": "Report not found"}), 404)
                database.update_report(report_id, status=status, priority=priority)
            except BadRequest:
                logger.warning("Invalid JSON in report update endpoint")
                return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
            except ReportNotFoundError as e:
                logger.info("Report not found for update", extra={"uuid": e.uuid})
                return make_response(jsonify({"message": "Report not found"}), 404)
            except Exception:
                logger.error("Error updating report", exc_info=True)
                return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
            return jsonify(database.get_report(report_id))

    return core_api_blueprint

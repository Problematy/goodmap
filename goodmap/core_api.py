import importlib.metadata
import logging
import uuid

import deprecation
import numpy
import pysupercluster
from flask import Blueprint, jsonify, make_response, request
from flask_babel import gettext
from platzky.config import LanguagesMapping
from spectree import Response, SpecTree
from werkzeug.exceptions import BadRequest

from goodmap.api_models import (
    ClusteringParams,
    CSRFTokenResponse,
    ErrorResponse,
    LocationReportRequest,
    LocationReportResponse,
    ReportUpdateRequest,
    SuggestionStatusRequest,
    SuccessResponse,
    VersionResponse,
)
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
from goodmap.json_security import JSONDepthError, JSONSizeError, safe_json_loads

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

    # Initialize Spectree for API documentation and validation
    # Use simple naming strategy without hashes for cleaner schema names
    spec = SpecTree(
        "flask",
        title="Goodmap API",
        version="0.1",
        path="doc",
        annotations=True,
        naming_strategy=lambda model: model.__name__,  # Use clean model names without hash
    )

    @core_api_blueprint.route("/suggest-new-point", methods=["POST"])
    @spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse))
    def suggest_new_point():
        """Suggest new location for review.

        Accepts location data either as JSON or multipart/form-data.
        All fields are validated using Pydantic location model.
        """
        import json as json_lib

        try:
            # Handle both multipart/form-data (with file uploads) and JSON
            if request.content_type and request.content_type.startswith("multipart/form-data"):
                # Parse form data dynamically
                suggested_location = {}

                for key in request.form:
                    value = request.form[key]
                    # Try to parse as JSON for complex types (arrays, objects, position)
                    try:
                        # SECURITY: Use safe_json_loads with depth/size limits
                        suggested_location[key] = safe_json_loads(value)
                    except (JSONDepthError, JSONSizeError) as e:
                        # Log security event and return 400
                        logger.warning(
                            f"JSON parsing blocked for security: {e}",
                            extra={"field": key, "value_size": len(value)},
                        )
                        return make_response(
                            jsonify({
                                "message": "Invalid request: JSON payload too complex or too large",
                                "error": str(e),
                            }),
                            400,
                        )
                    except ValueError:  # JSONDecodeError inherits from ValueError
                        # If not JSON, use as-is (simple string values)
                        suggested_location[key] = value

                # TODO: Handle photo file upload from request.files['photo']
                # For now, we just ignore it as the backend doesn't store photos yet
            else:
                # Parse JSON data
                suggested_location = request.get_json()

            suggested_location.update({"uuid": str(uuid.uuid4())})
            location = location_model.model_validate(suggested_location)
            database.add_suggestion(location.model_dump())
            message = (
                f"A new location has been suggested with details:"
                f"\n{json_lib.dumps(suggested_location, indent=2)}"
            )
            notifier_function(message)
        except BadRequest:
            logger.warning("Invalid request data in suggest endpoint")
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

    @core_api_blueprint.route("/report-location", methods=["POST"])
    @spec.validate(
        json=LocationReportRequest,
        resp=Response(HTTP_200=LocationReportResponse, HTTP_400=ErrorResponse),
    )
    def report_location():
        """Report a problem with a location.

        Allows users to report issues with existing locations,
        such as incorrect information or closed establishments.
        """
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

    @core_api_blueprint.route("/locations", methods=["GET"])
    @spec.validate()
    def get_locations():
        """Get list of locations with basic info.

        Returns locations filtered by query parameters,
        showing only uuid, position, and remark flag.
        """
        locations = get_locations_from_request(database, request.args, as_basic_info=True)
        return jsonify(locations)

    @core_api_blueprint.route("/locations-clustered", methods=["GET"])
    @spec.validate(resp=Response(HTTP_400=ErrorResponse))
    def get_locations_clustered():
        """Get clustered locations for map display.

        Returns locations grouped into clusters based on zoom level,
        optimized for rendering on interactive maps.
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

    @core_api_blueprint.route("/location/<location_id>", methods=["GET"])
    @spec.validate()
    def get_location(location_id):
        """Get detailed information for a single location.

        Returns full location data including all custom fields,
        formatted for display in the location details view.
        """
        location = database.get_location(location_id)
        visible_data = database.get_visible_data()
        meta_data = database.get_meta_data()

        formatted_data = prepare_pin(location.model_dump(), visible_data, meta_data)
        return jsonify(formatted_data)

    @core_api_blueprint.route("/version", methods=["GET"])
    @spec.validate(resp=Response(HTTP_200=VersionResponse))
    def get_version():
        """Get backend version information.

        Returns the current version of the Goodmap backend.
        """
        version_info = {"backend": importlib.metadata.version("goodmap")}
        return jsonify(version_info)

    @core_api_blueprint.route("/generate-csrf-token", methods=["GET"])
    @spec.validate(resp=Response(HTTP_200=CSRFTokenResponse))
    @deprecation.deprecated(
        deprecated_in="1.1.8",
        details="This endpoint for explicit CSRF token generation is deprecated. "
        "CSRF protection remains active in the application.",
    )
    def generate_csrf_token():
        """Generate CSRF token (DEPRECATED).

        This endpoint is deprecated and maintained only for backward compatibility.
        CSRF protection remains active in the application.
        """
        csrf_token = csrf_generator()
        return {"csrf_token": csrf_token}

    @core_api_blueprint.route("/categories", methods=["GET"])
    @spec.validate()
    def get_categories():
        """Get all available location categories.

        Returns list of categories with optional help text
        if CATEGORIES_HELP feature flag is enabled.
        """
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

    @core_api_blueprint.route("/languages", methods=["GET"])
    @spec.validate()
    def get_languages():
        """Get all available interface languages.

        Returns list of supported languages for the application.
        """
        return jsonify(languages)

    @core_api_blueprint.route("/category/<category_type>", methods=["GET"])
    @spec.validate()
    def get_category_types(category_type):
        """Get all available options for a specific category.

        Returns list of category options with optional help text
        if CATEGORIES_HELP feature flag is enabled.
        """
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

    @core_api_blueprint.route("/admin/locations", methods=["GET"])
    @spec.validate()
    def admin_get_locations():
        """Get paginated list of all locations for admin panel.

        Supports server-side pagination, sorting, and filtering.
        Defaults to sorting by name.
        """
        query_params = request.args.to_dict(flat=False)
        if "sort_by" not in query_params:
            query_params["sort_by"] = ["name"]
        result = database.get_locations_paginated(query_params)
        return jsonify(result)

    @core_api_blueprint.route("/admin/locations", methods=["POST"])
    @spec.validate(resp=Response(HTTP_400=ErrorResponse))
    def admin_create_location():
        """Create a new location (admin only).

        Validates location data using Pydantic model and
        adds it to the database.
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

    @core_api_blueprint.route("/admin/locations/<location_id>", methods=["PUT"])
    @spec.validate(resp=Response(HTTP_400=ErrorResponse, HTTP_404=ErrorResponse))
    def admin_update_location(location_id):
        """Update an existing location (admin only).

        Validates updated location data and persists changes.
        Returns 404 if location not found.
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

    @core_api_blueprint.route("/admin/locations/<location_id>", methods=["DELETE"])
    @spec.validate(resp=Response(HTTP_404=ErrorResponse))
    def admin_delete_location(location_id):
        """Delete a location (admin only).

        Permanently removes location from database.
        Returns 204 on success, 404 if not found.
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

    @core_api_blueprint.route("/admin/suggestions", methods=["GET"])
    @spec.validate()
    def admin_get_suggestions():
        """Get paginated list of location suggestions (admin only).

        Supports server-side pagination, sorting, and filtering by status.
        """
        query_params = request.args.to_dict(flat=False)
        result = database.get_suggestions_paginated(query_params)
        return jsonify(result)

    @core_api_blueprint.route("/admin/suggestions/<suggestion_id>", methods=["PUT"])
    @spec.validate(
        json=SuggestionStatusRequest,
        resp=Response(HTTP_400=ErrorResponse, HTTP_404=ErrorResponse, HTTP_409=ErrorResponse),
    )
    def admin_update_suggestion(suggestion_id):
        """Accept or reject a location suggestion (admin only).

        Accepted suggestions are added to locations database.
        Rejected suggestions are marked as rejected.
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

    @core_api_blueprint.route("/admin/reports", methods=["GET"])
    @spec.validate()
    def admin_get_reports():
        """Get paginated list of location reports (admin only).

        Supports server-side pagination, sorting,
        and filtering by status/priority.
        """
        query_params = request.args.to_dict(flat=False)
        result = database.get_reports_paginated(query_params)
        return jsonify(result)

    @core_api_blueprint.route("/admin/reports/<report_id>", methods=["PUT"])
    @spec.validate(
        json=ReportUpdateRequest,
        resp=Response(HTTP_400=ErrorResponse, HTTP_404=ErrorResponse),
    )
    def admin_update_report(report_id):
        """Update a report's status and/or priority (admin only).

        Allows changing report status to resolved/rejected
        and adjusting priority level.
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

    # Register Spectree with blueprint after all routes are defined
    spec.register(core_api_blueprint)

    # Add redirect from /doc to /doc/swagger/ for convenience
    @core_api_blueprint.route("/doc")
    def api_doc_redirect():
        """Redirect /api/doc to Swagger UI."""
        from flask import redirect
        return redirect("/api/doc/swagger/")

    return core_api_blueprint

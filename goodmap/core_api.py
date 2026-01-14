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

from goodmap.api_models import (
    CSRFTokenResponse,
    ErrorResponse,
    LocationReportRequest,
    LocationReportResponse,
    SuccessResponse,
    VersionResponse,
)
from goodmap.clustering import (
    map_clustering_data_to_proper_lazy_loading_object,
    match_clusters_uuids,
)
from goodmap.exceptions import LocationValidationError
from goodmap.formatter import prepare_pin
from goodmap.json_security import (
    MAX_JSON_DEPTH_LOCATION,
    JSONDepthError,
    JSONSizeError,
    safe_json_loads,
)

# SuperCluster configuration constants
MIN_ZOOM = 0
MAX_ZOOM = 16
CLUSTER_RADIUS = 200
CLUSTER_EXTENT = 512

# Error message constants
ERROR_INVALID_REQUEST_DATA = "Invalid request data"
ERROR_INVALID_LOCATION_DATA = "Invalid location data"
ERROR_LOCATION_NOT_FOUND = "Location not found"

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


def get_locations_from_request(database, request_args):
    """
    Shared helper to fetch locations from database based on request arguments.

    Args:
        database: Database instance
        request_args: Request arguments (flask.request.args)

    Returns:
        List of locations as basic_info dicts
    """
    query_params = request_args.to_dict(flat=False)
    all_locations = database.get_locations(query_params)
    return [x.basic_info() for x in all_locations]


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
    from typing import Any, Type

    def _clean_model_name(model: Type[Any]) -> str:
        return model.__name__

    spec = SpecTree(
        "flask",
        title="Goodmap API",
        version="0.1",
        path="doc",
        annotations=True,
        naming_strategy=_clean_model_name,  # Use clean model names without hash
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
                        # SECURITY: Use safe_json_loads with strict depth limit
                        # MAX_JSON_DEPTH_LOCATION=1: arrays/objects of primitives only
                        suggested_location[key] = safe_json_loads(
                            value, max_depth=MAX_JSON_DEPTH_LOCATION
                        )
                    except (JSONDepthError, JSONSizeError) as e:
                        # Log security event and return 400
                        logger.warning(
                            f"JSON parsing blocked for security: {e}",
                            extra={"field": key, "value_size": len(value)},
                        )
                        return make_response(
                            jsonify(
                                {
                                    "message": (
                                        "Invalid request: JSON payload too complex or too large"
                                    ),
                                    "error": str(e),
                                }
                            ),
                            400,
                        )
                    except ValueError:  # JSONDecodeError inherits from ValueError
                        # If not JSON, use as-is (simple string values)
                        suggested_location[key] = value

                # TODO: Handle photo file upload from request.files['photo']
                # For now, we just ignore it as the backend doesn't store photos yet
            else:
                # Parse JSON data with security checks (depth/size protection)
                raw_data = request.get_data(as_text=True)
                if not raw_data:
                    logger.warning("Empty JSON body in suggest endpoint")
                    return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
                try:
                    suggested_location = safe_json_loads(
                        raw_data, max_depth=MAX_JSON_DEPTH_LOCATION
                    )
                except (JSONDepthError, JSONSizeError) as e:
                    logger.warning(
                        f"JSON parsing blocked for security: {e}",
                        extra={"value_size": len(raw_data)},
                    )
                    return make_response(
                        jsonify(
                            {
                                "message": (
                                    "Invalid request: JSON payload too complex or too large"
                                ),
                                "error": str(e),
                            }
                        ),
                        400,
                    )
                except ValueError:
                    logger.warning("Invalid JSON in suggest endpoint")
                    return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
                if suggested_location is None:
                    logger.warning("Null JSON value in suggest endpoint")
                    return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)

            suggested_location.update({"uuid": str(uuid.uuid4())})
            location = location_model.model_validate(suggested_location)
            database.add_suggestion(location.model_dump())
            message = gettext("A new location has been suggested with details")
            notifier_message = f"{message}: {json_lib.dumps(suggested_location, indent=2)}"
            notifier_function(notifier_message)
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
        locations = get_locations_from_request(database, request.args)
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

            points = get_locations_from_request(database, request.args)
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
            return make_response(jsonify({"message": "An error occurred during clustering"}), 500)

    @core_api_blueprint.route("/location/<location_id>", methods=["GET"])
    @spec.validate(resp=Response(HTTP_404=ErrorResponse))
    def get_location(location_id):
        """Get detailed information for a single location.

        Returns full location data including all custom fields,
        formatted for display in the location details view.
        """
        location = database.get_location(location_id)
        if location is None:
            logger.info(ERROR_LOCATION_NOT_FOUND, extra={"uuid": location_id})
            return make_response(jsonify({"message": ERROR_LOCATION_NOT_FOUND}), 404)

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
            categories_help = category_data.get("categories_help")
            proper_categories_help = []
            if categories_help is not None:
                for option in categories_help:
                    proper_categories_help.append({option: gettext(f"categories_help_{option}")})

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

    # Register Spectree with blueprint after all routes are defined
    spec.register(core_api_blueprint)

    @core_api_blueprint.route("/doc")
    def api_doc_index():
        """Return links to available API documentation formats."""
        html = """<!DOCTYPE html>
<html><head><title>API Documentation</title></head>
<body>
<h1>API Documentation</h1>
<ul>
<li><a href="/api/doc/swagger/">Swagger UI</a></li>
<li><a href="/api/doc/redoc/">ReDoc</a></li>
<li><a href="/api/doc/openapi.json">OpenAPI JSON</a></li>
</ul>
</body></html>"""
        return html, 200, {"Content-Type": "text/html"}

    return core_api_blueprint

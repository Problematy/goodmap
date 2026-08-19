import importlib.metadata
import json as json_lib
import logging
import uuid
from typing import Any

import deprecation
import numpy
import pysupercluster
from flask import Blueprint, current_app, jsonify, make_response, request
from flask_babel import gettext
from platzky import FeatureFlagSet
from platzky.attachment import create_attachment
from platzky.config import AttachmentConfig, LanguagesMapping
from platzky.shortcodes import Shortcode
from spectree import Response, SpecTree
from spectree.models import Tag
from werkzeug.exceptions import HTTPException

from goodmap.api.api_models import (
    CategoriesFullResponse,
    ClusteringParams,
    ClusterList,
    ErrorResponse,
    LanguagesResponse,
    LocationDetail,
    LocationList,
    LocationQueryParams,
    LocationReportRequest,
    LocationReportResponse,
    LocationSchemaResponse,
    SuccessResponse,
    VersionResponse,
)
from goodmap.clustering import (
    map_clustering_data_to_proper_lazy_loading_object,
    match_clusters_uuids,
)
from goodmap.exceptions import LocationValidationError
from goodmap.feature_flags import CategoriesHelp
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

# Report description validation constants
MAX_DESCRIPTION_LENGTH = 500

# Error message constants
ERROR_INVALID_REQUEST_DATA = "Invalid request data"
ERROR_INVALID_LOCATION_DATA = "Invalid location data"
ERROR_LOCATION_NOT_FOUND = "Location not found"
ERROR_INVALID_DESCRIPTION = "Invalid report description"

logger = logging.getLogger(__name__)

# The API surface - paths, methods, response envelopes, status codes - is the same in
# every deployment. The *values* flowing through it are not: filters, accepted point
# fields and reportable issues all come from that deployment's own data source. These
# tags group the endpoints in /api/doc so that split is visible, and point at the
# discovery endpoints that report what a given instance actually declares.
TAG_DISCOVERY = Tag(
    name="discovery",
    description="What this particular deployment declares - call these to find out, "
    "rather than assuming; the answers differ between instances.",
)
TAG_MAP_DATA = Tag(
    name="map data",
    description="Reading points. Response envelopes are fixed; which filters apply and "
    "which fields come back depend on this deployment's data source.",
)
TAG_SUBMISSIONS = Tag(
    name="submissions",
    description="Visitor-submitted points and reports. Both land in a moderation queue "
    "and need a CSRF token.",
)
TAG_META = Tag(name="meta", description="Fixed in every deployment.")


@deprecation.deprecated(
    deprecated_in="1.5.0",
    removed_in="2.0.0",
    details="Configure 'reported_issue_types' in the database instead. "
    "The hardcoded fallback will be removed in a future release.",
)
def get_default_issue_options():
    """Return hardcoded fallback issue options for backward compatibility."""
    return ["notHere", "overload", "broken", "other"]


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


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


def safe_location_loads(raw_location: str) -> dict[str, Any]:
    """Parse a suggested-location payload, requiring it to be a JSON object.

    Raises JSONDepthError/JSONSizeError for DoS-shaped payloads, or ValueError
    for ordinary malformed JSON or a non-object payload - same as safe_json_loads,
    plus the object-shape requirement.
    """
    parsed = safe_json_loads(raw_location, max_depth=MAX_JSON_DEPTH_LOCATION)
    if not isinstance(parsed, dict):
        raise ValueError("Location payload is not a JSON object")
    return parsed


def core_pages(
    database,
    languages: LanguagesMapping,
    notifier_function,
    location_model,
    photo_attachment_config: AttachmentConfig,
    feature_flags: FeatureFlagSet,
    shortcodes: dict[str, Shortcode],
) -> Blueprint:
    core_api_blueprint = Blueprint("api", __name__, url_prefix="/api")

    # Build photo error message from config
    allowed_ext = ", ".join(sorted(photo_attachment_config.allowed_extensions or []))
    max_size_mb = photo_attachment_config.max_size / (1024 * 1024)
    error_invalid_photo = (
        f"Invalid photo. Allowed formats: {allowed_ext}. Max size: {max_size_mb:.0f}MiB."
    )

    # Initialize Spectree for API documentation and validation
    def _clean_model_name(model: type) -> str:
        return model.__name__

    spec = SpecTree(
        "flask",
        title="Goodmap API",
        version="0.1",
        path="doc",
        # annotations=False: the handlers take no model-annotated parameters, and with
        # it on spectree refuses skip_validation, which several routes below rely on.
        annotations=False,
        naming_strategy=_clean_model_name,  # Use clean model names without hash
        tags=[TAG_DISCOVERY, TAG_MAP_DATA, TAG_SUBMISSIONS, TAG_META],
    )

    @core_api_blueprint.route("/suggest-new-point", methods=["POST"])
    # No form= model: the point's fields are the deployment's own location_model, so a
    # static schema could only say "location is a string" - which the docstring already
    # says, in words, without spectree then 500ing on an attached photo it cannot
    # serialize into a validation error. The handler validates against location_model.
    @spec.validate(
        tags=[TAG_SUBMISSIONS], resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse)
    )
    def suggest_new_point():
        """Suggest new location for review.

        Accepts multipart/form-data with the location data as a JSON object in the
        'location' field, plus an optional binary 'photo' file. All fields are
        validated using the Pydantic location model.
        """
        try:
            photo_attachment = None
            raw_location = request.form.get("location", "")
            try:
                suggested_location = safe_location_loads(raw_location)
            except (JSONDepthError, JSONSizeError) as e:
                # Log security event and return 400
                logger.warning(
                    f"JSON parsing blocked for security: {e}",
                    extra={"value_size": len(raw_location)},
                )
                return make_response(
                    jsonify(
                        {
                            "message": "Invalid request: JSON payload too complex or too large",
                        }
                    ),
                    400,
                )
            except ValueError:
                logger.warning("Invalid location payload in suggest endpoint")
                return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)

            # Extract and validate photo attachment if present
            photo_file = request.files.get("photo")
            if photo_file and photo_file.filename:
                photo_content = photo_file.read()
                photo_mime = photo_file.content_type or "application/octet-stream"

                try:
                    photo_attachment = create_attachment(
                        photo_file.filename, photo_content, photo_mime, photo_attachment_config
                    )
                except ValueError as e:
                    logger.warning(
                        "Rejected photo: %s",
                        e,
                        extra={"photo_filename": repr(photo_file.filename)},
                    )
                    return make_response(jsonify({"message": error_invalid_photo}), 400)

            suggested_location.update({"uuid": str(uuid.uuid4())})
            location = location_model.model_validate(suggested_location)
            database.add_suggestion(location.model_dump())
            message = gettext("A new location has been suggested with details")
            notifier_message = f"{message}: {json_lib.dumps(suggested_location, indent=2)}"
            attachments = frozenset({photo_attachment}) if photo_attachment else frozenset()
            notifier_function(notifier_message, attachments=attachments)
        except LocationValidationError as e:
            # NOTE: validation_errors includes input values from the location model fields:
            # - Core fields: position (lat/long), uuid, remark
            # - Dynamic fields: categories and obligatory_fields configured per deployment
            # These are geographic/categorical data, NOT PII (no email, phone, names of people).
            # Safe to log for debugging. If PII fields are ever added to the location model,
            # strip 'input' from validation_errors before logging.
            logger.warning(
                "Location validation failed in suggest endpoint: %s",
                e.validation_errors,
                extra={"errors": e.validation_errors},
            )
            return make_response(jsonify({"message": ERROR_INVALID_LOCATION_DATA}), 400)
        except HTTPException:
            # Carries its own status (e.g. 413 for a body past MAX_CONTENT_LENGTH);
            # reporting it as a 500 would misattribute a client error to the server.
            raise
        except Exception:
            logger.exception("Error in suggest location endpoint")
            return make_response(
                jsonify({"message": "An error occurred while processing your suggestion"}), 500
            )
        return make_response(jsonify({"message": "Location suggested"}), 200)

    @core_api_blueprint.route("/report-location", methods=["POST"])
    @spec.validate(
        tags=[TAG_SUBMISSIONS],
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
            description = location_report["description"]

            # Validate description against configured issue options
            issue_options = database.get_issue_options()
            if not issue_options:
                issue_options = get_default_issue_options()

            if description not in issue_options:
                if "other" not in issue_options:
                    return make_response(jsonify({"message": ERROR_INVALID_DESCRIPTION}), 400)
                if len(description) > MAX_DESCRIPTION_LENGTH:
                    return make_response(jsonify({"message": ERROR_INVALID_DESCRIPTION}), 400)

            report = {
                "uuid": str(uuid.uuid4()),
                "location_id": location_report["id"],
                "description": description,
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
            logger.exception("Error in report location endpoint")
            error_message = gettext("Error sending notification")
            return make_response(jsonify({"message": error_message}), 500)
        return make_response(jsonify({"message": gettext("Location reported")}), 200)

    @core_api_blueprint.route("/locations", methods=["GET"])
    # skip_validation: this endpoint ignores invalid and unknown query parameters by
    # design, so spectree must document them without rejecting anything.
    @spec.validate(
        tags=[TAG_MAP_DATA],
        query=LocationQueryParams,
        resp=Response(HTTP_200=LocationList),
        skip_validation=True,
    )
    def get_locations():
        """Get list of locations with basic info.

        Returns locations filtered by query parameters,
        showing only uuid, position, and whether each has a remark.
        """
        locations = get_locations_from_request(database, request.args)
        return jsonify(locations)

    @core_api_blueprint.route("/locations-clustered", methods=["GET"])
    # skip_validation: the handler owns zoom validation and returns 400 with a log line;
    # letting spectree validate would turn that into a 422 and skip the log.
    @spec.validate(
        tags=[TAG_MAP_DATA],
        query=ClusteringParams,
        resp=Response(HTTP_200=ClusterList, HTTP_400=ErrorResponse),
        skip_validation=True,
    )
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
            logger.exception("Clustering operation failed: %s", e)
            return make_response(jsonify({"message": "An error occurred during clustering"}), 500)

    @core_api_blueprint.route("/location/<uuid:location_id>", methods=["GET"])
    @spec.validate(
        tags=[TAG_MAP_DATA], resp=Response(HTTP_200=LocationDetail, HTTP_404=ErrorResponse)
    )
    def get_location(location_id):
        """Get detailed information for a single location.

        The ``<uuid:...>`` converter accepts only valid UUIDs; non-UUID ids 404
        at routing. goodmap 2.0.0 dropped support for non-UUID location ids.

        Returns full location data including all custom fields,
        formatted for display in the location details view.
        """
        location_id = str(location_id)
        location = database.get_location(location_id)
        if location is None:
            logger.info(ERROR_LOCATION_NOT_FOUND, extra={"uuid": location_id})
            return make_response(jsonify({"message": ERROR_LOCATION_NOT_FOUND}), 404)

        visible_data = database.get_visible_data()
        meta_data = database.get_meta_data()
        formatted_data = prepare_pin(location.model_dump(), visible_data, meta_data, shortcodes)
        return jsonify(formatted_data)

    @core_api_blueprint.route("/version", methods=["GET"])
    @spec.validate(tags=[TAG_META], resp=Response(HTTP_200=VersionResponse))
    def get_version():
        """Get backend version information.

        Returns the current version of the Goodmap backend.
        """
        version_info = {"backend": importlib.metadata.version("goodmap")}
        return jsonify(version_info)

    @core_api_blueprint.route("/location-schema", methods=["GET"])
    @spec.validate(tags=[TAG_DISCOVERY], resp=Response(HTTP_200=LocationSchemaResponse))
    def get_location_schema():
        """Get the schema this instance accepts for a new point.

        The fields a point may carry are configured per deployment, so there is no
        fixed payload for /api/suggest-new-point. This returns the accepted fields
        (excluding only the server-assigned uuid - position is required and must be
        supplied by the client), the allowed values for each category, the reportable
        issue types and the photo limits, as the built-in suggest form uses them.
        """
        category_data = database.get_category_data()
        properties = location_model.model_json_schema().get("properties", {})
        # Matches the fallback /api/report-location applies: an unconfigured
        # reported_issue_types must not make this endpoint advertise fewer accepted
        # values than the report endpoint actually accepts.
        issue_options = database.get_issue_options() or get_default_issue_options()
        return jsonify(
            {
                "fields": {name: spec_ for name, spec_ in properties.items() if name != "uuid"},
                "obligatory_fields": current_app.extensions.get("goodmap", {}).get(
                    "location_obligatory_fields", []
                ),
                "categories": category_data.get("categories", {}),
                "reported_issue_types": [{"value": t, "label": gettext(t)} for t in issue_options],
                "photo": {
                    "allowed_extensions": sorted(photo_attachment_config.allowed_extensions or []),
                    "allowed_mime_types": sorted(photo_attachment_config.allowed_mime_types or []),
                    "max_size_bytes": photo_attachment_config.max_size,
                },
            }
        )

    @core_api_blueprint.route("/categories-full", methods=["GET"])
    @spec.validate(tags=[TAG_DISCOVERY], resp=Response(HTTP_200=CategoriesFullResponse))
    def get_categories_full():
        """Get all categories with their subcategory options in a single request.

        Returns combined category data to reduce API calls for filter panel loading.
        This endpoint eliminates the need for multiple sequential requests.
        """
        categories_data = database.get_category_data()
        result = []

        categories_options_help = categories_data.get("categories_options_help", {})
        categories_default_checked = categories_data.get("categories_default_checked", {})
        categories_filter_mode = categories_data.get("categories_filter_mode", {})

        for key, options in categories_data["categories"].items():
            category_entry = {
                "key": key,
                "name": gettext(key),
                "options": make_tuple_translation(options),
                "default_checked": [
                    option
                    for option in categories_default_checked.get(key, [])
                    if option in options
                ],
                "filter_mode": categories_filter_mode.get(key, "or"),
            }

            if CategoriesHelp in feature_flags:
                option_help_list = categories_options_help.get(key, [])
                proper_options_help = []
                for option in option_help_list:
                    proper_options_help.append(
                        {option: gettext(f"categories_options_help_{option}")}
                    )
                category_entry["options_help"] = proper_options_help

            result.append(category_entry)

        response = {"categories": result}

        if CategoriesHelp in feature_flags:
            categories_help = categories_data.get("categories_help", [])
            proper_categories_help = []
            for option in categories_help:
                proper_categories_help.append({option: gettext(f"categories_help_{option}")})
            response["categories_help"] = proper_categories_help

        return jsonify(response)

    @core_api_blueprint.route("/languages", methods=["GET"])
    @spec.validate(tags=[TAG_DISCOVERY], resp=Response(HTTP_200=LanguagesResponse))
    def get_languages():
        """Get all available interface languages.

        Returns list of supported languages for the application.
        """
        return jsonify(languages)

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

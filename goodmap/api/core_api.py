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
    ClusteredQueryParams,
    ClusterList,
    ErrorResponse,
    LanguagesResponse,
    LocationDetail,
    LocationList,
    LocationQueryParams,
    LocationReportRequest,
    LocationReportResponse,
    LocationSchemaResponse,
    PinMarkerFields,
    SuccessResponse,
    VersionResponse,
    marker_style_values,
)
from goodmap.clustering import (
    MAX_ZOOM,
    MIN_ZOOM,
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

CLUSTER_RADIUS = 200
CLUSTER_EXTENT = 512

# Report description validation constants
MAX_DESCRIPTION_LENGTH = 500

# Error message constants
ERROR_INVALID_REQUEST_DATA = "Invalid request data"
ERROR_INVALID_LOCATION_DATA = "Invalid location data"
ERROR_LOCATION_NOT_FOUND = "Location not found"
ERROR_INVALID_DESCRIPTION = "Invalid report description"
ERROR_INVALID_PARAMETERS = "Invalid parameters provided"
ERROR_PAYLOAD_TOO_COMPLEX = "Invalid request: JSON payload too complex or too large"
ERROR_CLUSTERING_FAILED = "An error occurred during clustering"
ERROR_SUGGESTION_FAILED = "An error occurred while processing your suggestion"

logger = logging.getLogger(__name__)

# The API surface - paths, methods, response shapes, status codes - is the same in
# every deployment. The *values* flowing through it are not: filters, accepted point
# fields and reportable issues all come from that deployment's own data source. These
# tags group the endpoints in /api/doc so that split is visible, and point at the
# endpoints that report what a given instance actually declares.
TAG_DEPLOYMENT_SPECIFIC = Tag(
    name="deployment_specific",
    description="What this particular deployment declares - call these to find out, "
    "rather than assuming; the answers differ between instances.",
)
TAG_MAP_DATA = Tag(
    name="map data",
    description="Reading points. Response shapes are fixed; which filters apply and "
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


def translated_help(options, prefix: str) -> list[dict[str, str]]:
    """Build the ``[{option: help text}]`` shape the help fields use.

    The help text is looked up under ``<prefix>_<option>``, so the data source only
    stores which options have help, not the text itself.
    """
    return [{option: gettext(f"{prefix}_{option}")} for option in options or []]


def api_error(message: str, status: int):
    """Build the API's standard error response: a JSON body of just {"message": ...}."""
    return make_response(jsonify({"message": message}), status)


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def get_locations_from_request(database, request_args, pin_marker_fields):
    """
    Shared helper to fetch locations from database based on request arguments.

    Args:
        database: Database instance
        request_args: Request arguments (flask.request.args)
        pin_marker_fields: This deployment's marker_styles icon_field/color_field
            names - merged into each location's basic_info as a nested `marker`
            object so the frontend can style pins without a further per-location
            request.

    Returns:
        List of locations as basic_info dicts, each merged with marker_style_values.
    """
    query_params = request_args.to_dict(flat=False)
    all_locations = database.get_locations(query_params)
    return [
        {**location.basic_info(), **marker_style_values(location, pin_marker_fields)}
        for location in all_locations
    ]


def photo_attachment_from_request(photo_attachment_config: AttachmentConfig):
    """Build the attachment for the request's optional ``photo`` part, or None.

    Raises ValueError, from create_attachment, if the photo breaks the configured
    format or size limits - the caller answers with the configured message.
    """
    photo_file = request.files.get("photo")
    if not (photo_file and photo_file.filename):
        return None
    content = photo_file.read()
    mime = photo_file.content_type or "application/octet-stream"
    return create_attachment(photo_file.filename, content, mime, photo_attachment_config)


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


def _validation_error_to_api_shape(req, resp, req_validation_error, instance):
    """Rewrite spectree's raw pydantic error into the API's documented error shape.

    Spectree answers a failed request model with a bare list of pydantic error dicts,
    which contradicts the "errors are {"message": ...}" contract every other endpoint
    keeps, and leaks input values and errors.pydantic.dev links to the caller. The
    detail goes to the log instead, same as the handlers' own error paths.
    """
    if req_validation_error is None or resp is None:
        return
    errors = req_validation_error.errors()
    logger.warning(
        "Request validation failed: %s",
        errors,
        extra={"path": getattr(req, "path", None)},
    )
    # Name the offending parameters but not their values or pydantic's internals: the
    # caller sent those names, so echoing them back leaks nothing and saves a guess.
    fields = sorted({str(loc) for e in errors for loc in e.get("loc", ())})
    body = {"message": ERROR_INVALID_REQUEST_DATA}
    if fields:
        body["error"] = f"invalid or out of range: {', '.join(fields)}"
    resp.set_data(json_lib.dumps(body))
    resp.content_type = "application/json"


def core_pages(
    database,
    languages: LanguagesMapping,
    notifier_function,
    location_model,
    photo_attachment_config: AttachmentConfig,
    feature_flags: FeatureFlagSet,
    shortcodes: dict[str, Shortcode],
    pin_marker_fields: PinMarkerFields,
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
        naming_strategy=_clean_model_name,  # Use clean model names without hash
        tags=[TAG_DEPLOYMENT_SPECIFIC, TAG_MAP_DATA, TAG_SUBMISSIONS, TAG_META],
        validation_error_status=400,
        validation_error_model=ErrorResponse,
        before=_validation_error_to_api_shape,
    )

    @core_api_blueprint.route("/suggest-new-point", methods=["POST"])
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
            raw_location = request.form.get("location", "")
            try:
                suggested_location = safe_location_loads(raw_location)
            except (JSONDepthError, JSONSizeError) as e:
                # Log security event and return 400
                logger.warning(
                    f"JSON parsing blocked for security: {e}",
                    extra={"value_size": len(raw_location)},
                )
                return api_error(ERROR_PAYLOAD_TOO_COMPLEX, 400)
            except ValueError:
                logger.warning("Invalid location payload in suggest endpoint")
                return api_error(ERROR_INVALID_REQUEST_DATA, 400)

            try:
                photo_attachment = photo_attachment_from_request(photo_attachment_config)
            except ValueError as e:
                logger.warning(
                    "Rejected photo: %s",
                    e,
                    extra={"photo_filename": repr(request.files["photo"].filename)},
                )
                return api_error(error_invalid_photo, 400)

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
            return api_error(ERROR_INVALID_LOCATION_DATA, 400)
        except HTTPException:
            # Carries its own status (e.g. 413 for a body past MAX_CONTENT_LENGTH);
            # reporting it as a 500 would misattribute a client error to the server.
            raise
        except Exception:
            logger.exception("Error in suggest location endpoint")
            return api_error(ERROR_SUGGESTION_FAILED, 500)
        return api_error("Location suggested", 200)

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
                    return api_error(ERROR_INVALID_DESCRIPTION, 400)
                if len(description) > MAX_DESCRIPTION_LENGTH:
                    return api_error(ERROR_INVALID_DESCRIPTION, 400)

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
            return api_error(error_message, 500)
        return api_error(gettext("Location reported"), 200)

    @core_api_blueprint.route("/locations", methods=["GET"])
    @spec.validate(
        tags=[TAG_MAP_DATA],
        query=LocationQueryParams,
        resp=Response(HTTP_200=LocationList, HTTP_400=ErrorResponse),
    )
    def get_locations():
        """Get list of locations with basic info.

        Returns locations filtered by query parameters: uuid, position, and a
        `marker` object (icon/color/badge) with everything needed to render a
        styled pin.
        """
        locations = get_locations_from_request(database, request.args, pin_marker_fields)
        return jsonify(locations)

    @core_api_blueprint.route("/locations-clustered", methods=["GET"])
    @spec.validate(
        tags=[TAG_MAP_DATA],
        query=ClusteredQueryParams,
        resp=Response(HTTP_200=ClusterList, HTTP_400=ErrorResponse),
    )
    def get_locations_clustered():
        """Get clustered locations for map display.

        Returns locations grouped into clusters based on zoom level,
        optimized for rendering on interactive maps.
        """
        try:
            query_params = request.args.to_dict(flat=False)
            zoom = int(query_params.get("zoom", [7])[0])

            points = get_locations_from_request(database, request.args, pin_marker_fields)
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
            return api_error(ERROR_INVALID_PARAMETERS, 400)
        except Exception as e:
            logger.exception("Clustering operation failed: %s", e)
            return api_error(ERROR_CLUSTERING_FAILED, 500)

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
            return api_error(ERROR_LOCATION_NOT_FOUND, 404)

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
    @spec.validate(tags=[TAG_DEPLOYMENT_SPECIFIC], resp=Response(HTTP_200=LocationSchemaResponse))
    def get_location_schema():
        """Get the schema this instance accepts for a new point.

        The fields a point may carry are configured per deployment, so there is no
        fixed payload for /api/suggest-new-point. This returns the accepted fields
        (excluding only the server-assigned uuid - position is required and must be
        supplied by the client), the reportable issue types and the photo limits, as
        the built-in suggest form uses them.

        A field's own allowed values are part of its schema under `fields`. What this no
        longer carries is a separate top-level `categories` map repeating them in another
        shape; /api/categories-full reports the same values with translated labels.
        """
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
                "reported_issue_types": [{"value": t, "label": gettext(t)} for t in issue_options],
                "photo": {
                    "allowed_extensions": sorted(photo_attachment_config.allowed_extensions or []),
                    "allowed_mime_types": sorted(photo_attachment_config.allowed_mime_types or []),
                    "max_size_bytes": photo_attachment_config.max_size,
                },
            }
        )

    @core_api_blueprint.route("/categories-full", methods=["GET"])
    @spec.validate(tags=[TAG_DEPLOYMENT_SPECIFIC], resp=Response(HTTP_200=CategoriesFullResponse))
    def get_categories_full():
        """Get all categories with their subcategory options in a single request.

        Returns combined category data to reduce API calls for filter panel loading.
        This endpoint eliminates the need for multiple sequential requests.
        """
        categories_data = database.get_category_data()
        with_help = CategoriesHelp in feature_flags
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

            if with_help:
                category_entry["options_help"] = translated_help(
                    categories_options_help.get(key), "categories_options_help"
                )

            result.append(category_entry)

        response = {"categories": result}

        if with_help:
            response["categories_help"] = translated_help(
                categories_data.get("categories_help"), "categories_help"
            )

        return jsonify(response)

    @core_api_blueprint.route("/languages", methods=["GET"])
    @spec.validate(tags=[TAG_DEPLOYMENT_SPECIFIC], resp=Response(HTTP_200=LanguagesResponse))
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

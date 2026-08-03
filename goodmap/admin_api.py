import logging
import uuid
from typing import Any, Type

from flask import Blueprint, jsonify, make_response, request
from spectree import Response, SpecTree
from werkzeug.exceptions import BadRequest

from goodmap.api_models import (
    ErrorResponse,
    ReportUpdateRequest,
    SuggestionStatusRequest,
)
from goodmap.exceptions import (
    LocationAlreadyExistsError,
    LocationNotFoundError,
    LocationValidationError,
    ReportNotFoundError,
)

# Error message constants
ERROR_INVALID_REQUEST_DATA = "Invalid request data"
ERROR_INVALID_LOCATION_DATA = "Invalid location data"
ERROR_INTERNAL_ERROR = "An internal error occurred"
ERROR_LOCATION_NOT_FOUND = "Location not found"

logger = logging.getLogger(__name__)


def _clean_model_name(model: Type[Any]) -> str:
    return model.__name__


def _handle_location_validation_error(e: LocationValidationError):
    """Handle LocationValidationError and return appropriate response."""
    logger.warning(
        "Location validation failed - uuid: %s, errors: %s",
        e.uuid,
        e.validation_errors,
        extra={"uuid": e.uuid, "errors": e.validation_errors},
    )
    return make_response(jsonify({"message": ERROR_INVALID_LOCATION_DATA}), 400)


def _get_locations_handler(database):
    """Handle GET /locations request."""
    query_params = request.args.to_dict(flat=False)
    if "sort_by" not in query_params:
        query_params["sort_by"] = ["name"]
    result = database.get_locations_paginated(query_params)
    return jsonify(result)


def _create_location_handler(database, location_model):
    """Handle POST /locations request."""
    location_data = request.get_json()
    if location_data is None:
        logger.warning("Empty or invalid JSON in admin create location endpoint")
        return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
    # TODO: Catch pydantic.ValidationError separately to return 400 instead of 500
    try:
        location_data.update({"uuid": str(uuid.uuid4())})
        location = location_model.model_validate(location_data)
        database.add_location(location.model_dump())
    except LocationValidationError as e:
        return _handle_location_validation_error(e)
    except Exception:
        logger.error("Error creating location", exc_info=True)
        return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
    return jsonify(location.model_dump())


def _update_location_handler(database, location_model, location_id):
    """Handle PUT /locations/<location_id> request."""
    location_data = request.get_json()
    if location_data is None:
        logger.warning("Empty or invalid JSON in admin update location endpoint")
        return make_response(jsonify({"message": ERROR_INVALID_REQUEST_DATA}), 400)
    # TODO: Catch pydantic.ValidationError separately to return 400 instead of 500
    try:
        location_data.update({"uuid": location_id})
        location = location_model.model_validate(location_data)
        database.update_location(location_id, location.model_dump())
    except LocationValidationError as e:
        return _handle_location_validation_error(e)
    except LocationNotFoundError as e:
        logger.info("Location not found for update", extra={"uuid": e.uuid})
        return make_response(jsonify({"message": ERROR_LOCATION_NOT_FOUND}), 404)
    except Exception:
        logger.error("Error updating location", exc_info=True)
        return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
    return jsonify(location.model_dump())


def _delete_location_handler(database, location_id):
    """Handle DELETE /locations/<location_id> request."""
    try:
        database.delete_location(location_id)
    except LocationNotFoundError as e:
        logger.info("Location not found for deletion", extra={"uuid": e.uuid})
        return make_response(jsonify({"message": ERROR_LOCATION_NOT_FOUND}), 404)
    except Exception:
        logger.error("Error deleting location", exc_info=True)
        return make_response(jsonify({"message": ERROR_INTERNAL_ERROR}), 500)
    return "", 204


def _get_suggestions_handler(database):
    """Handle GET /suggestions request."""
    query_params = request.args.to_dict(flat=False)
    result = database.get_suggestions_paginated(query_params)
    return jsonify(result)


def _update_suggestion_handler(database, suggestion_id):
    """Handle PUT /suggestions/<suggestion_id> request."""
    try:
        data = request.get_json()
        status = data["status"]  # Validated by Spectree
        suggestion = database.get_suggestion(suggestion_id)
        if not suggestion:
            return make_response(jsonify({"message": "Suggestion not found"}), 404)
        if suggestion.get("status") != "pending":
            return make_response(jsonify({"message": "Suggestion already processed"}), 409)
        if status == "accepted":
            suggestion_data = {k: v for k, v in suggestion.items() if k != "status"}
            database.add_location(suggestion_data)
        database.update_suggestion(suggestion_id, status)
    except LocationValidationError as e:
        logger.warning(
            "Location validation failed in suggestion - uuid: %s, errors: %s",
            e.uuid,
            e.validation_errors,
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


def _get_reports_handler(database):
    """Handle GET /reports request."""
    query_params = request.args.to_dict(flat=False)
    result = database.get_reports_paginated(query_params)
    return jsonify(result)


def _update_report_handler(database, report_id):
    """Handle PUT /reports/<report_id> request."""
    try:
        data = request.get_json()
        status = data.get("status")
        priority = data.get("priority")
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


def admin_pages(database, location_model) -> Blueprint:
    """Create and return the admin API blueprint.

    Args:
        database: Database instance for data operations
        location_model: Pydantic model for location validation

    Returns:
        Blueprint: Flask blueprint with all admin endpoints
    """
    admin_api_blueprint = Blueprint("admin_api", __name__, url_prefix="/api/admin")

    spec = SpecTree(
        "flask",
        title="Goodmap Admin API",
        version="0.1",
        path="doc",
        annotations=True,
        naming_strategy=_clean_model_name,
    )

    @admin_api_blueprint.route("/locations", methods=["GET"])
    @spec.validate()
    def admin_get_locations():
        """Get paginated list of all locations for admin panel."""
        return _get_locations_handler(database)

    @admin_api_blueprint.route("/locations", methods=["POST"])
    @spec.validate(resp=Response(HTTP_400=ErrorResponse))
    def admin_create_location():
        """Create a new location (admin only)."""
        return _create_location_handler(database, location_model)

    @admin_api_blueprint.route("/locations/<location_id>", methods=["PUT"])
    @spec.validate(resp=Response(HTTP_400=ErrorResponse, HTTP_404=ErrorResponse))
    def admin_update_location(location_id):
        """Update an existing location (admin only)."""
        return _update_location_handler(database, location_model, location_id)

    @admin_api_blueprint.route("/locations/<location_id>", methods=["DELETE"])
    @spec.validate(resp=Response(HTTP_404=ErrorResponse))
    def admin_delete_location(location_id):
        """Delete a location (admin only)."""
        return _delete_location_handler(database, location_id)

    @admin_api_blueprint.route("/suggestions", methods=["GET"])
    @spec.validate()
    def admin_get_suggestions():
        """Get paginated list of location suggestions (admin only)."""
        return _get_suggestions_handler(database)

    @admin_api_blueprint.route("/suggestions/<suggestion_id>", methods=["PUT"])
    @spec.validate(
        json=SuggestionStatusRequest,
        resp=Response(HTTP_400=ErrorResponse, HTTP_404=ErrorResponse, HTTP_409=ErrorResponse),
    )
    def admin_update_suggestion(suggestion_id):
        """Accept or reject a location suggestion (admin only)."""
        return _update_suggestion_handler(database, suggestion_id)

    @admin_api_blueprint.route("/reports", methods=["GET"])
    @spec.validate()
    def admin_get_reports():
        """Get paginated list of location reports (admin only)."""
        return _get_reports_handler(database)

    @admin_api_blueprint.route("/reports/<report_id>", methods=["PUT"])
    @spec.validate(
        json=ReportUpdateRequest,
        resp=Response(HTTP_400=ErrorResponse, HTTP_404=ErrorResponse),
    )
    def admin_update_report(report_id):
        """Update a report's status and/or priority (admin only)."""
        return _update_report_handler(database, report_id)

    # Register Spectree with blueprint after all routes are defined
    spec.register(admin_api_blueprint)

    return admin_api_blueprint

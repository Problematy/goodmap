import importlib.metadata
import uuid

from flask import Blueprint, jsonify, make_response, request
from flask_babel import gettext
from flask_restx import Api, Resource, fields
from platzky.config import LanguagesMapping

from goodmap.formatter import prepare_pin


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def get_or_none(data, *keys):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data


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
            except ValueError as e:
                return make_response(jsonify({"message": f"Invalid location data: {e}"}), 400)
            except Exception as e:
                return make_response(jsonify({"message": f"Error sending notification : {e}"}), 400)
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
            except KeyError as e:
                error_message = gettext("Error reporting location")
                return make_response(jsonify({"message": f"{error_message} : {e}"}), 400)
            except Exception as e:
                error_message = gettext("Error sending notification")
                return make_response(jsonify({"message": f"{error_message} : {e}"}), 400)
            return make_response(jsonify({"message": gettext("Location reported")}), 200)

    @core_api.route("/locations")
    class GetLocations(Resource):
        def get(self):
            """
            Shows list of locations with uuid and position
            """
            query_params = request.args.to_dict(flat=False)
            all_locations = database.get_locations(query_params)
            return jsonify([x.basic_info() for x in all_locations])

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
            except ValueError as e:
                return make_response(jsonify({"message": f"Invalid location data: {e}"}), 400)
            except Exception as e:
                return make_response(jsonify({"message": f"Error creating location: {e}"}), 400)
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
            except ValueError as e:
                return make_response(jsonify({"message": f"Invalid location data: {e}"}), 400)
            except Exception as e:
                return make_response(jsonify({"message": f"Error updating location: {e}"}), 400)
            return jsonify(location.model_dump())

        def delete(self, location_id):
            """
            Deletes a single location
            """
            try:
                database.delete_location(location_id)
            except ValueError as e:
                return make_response(jsonify({"message": f"Location not found: {e}"}), 404)
            except Exception as e:
                return make_response(jsonify({"message": f"Error deleting location: {e}"}), 400)
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
                    return make_response(jsonify({"message": f"Invalid status: {status}"}), 400)
                suggestion = database.get_suggestion(suggestion_id)
                if not suggestion:
                    return make_response(jsonify({"message": "Suggestion not found"}), 404)
                if suggestion.get("status") != "pending":
                    return make_response(jsonify({"message": "Suggestion already processed"}), 400)
                if status == "accepted":
                    suggestion_data = {k: v for k, v in suggestion.items() if k != "status"}
                    database.add_location(suggestion_data)
                database.update_suggestion(suggestion_id, status)
            except ValueError as e:
                return make_response(jsonify({"message": f"{e}"}), 400)
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
                    return make_response(jsonify({"message": f"Invalid status: {status}"}), 400)
                if priority and priority not in valid_priority:
                    return make_response(jsonify({"message": f"Invalid priority: {priority}"}), 400)
                report = database.get_report(report_id)
                if not report:
                    return make_response(jsonify({"message": "Report not found"}), 404)
                database.update_report(report_id, status=status, priority=priority)
            except ValueError as e:
                return make_response(jsonify({"message": f"{e}"}), 400)
            return jsonify(database.get_report(report_id))

    return core_api_blueprint

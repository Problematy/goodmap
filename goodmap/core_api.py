import importlib.metadata
import uuid

from flask import Blueprint, jsonify, make_response, request
from flask_babel import gettext
from flask_restx import Api, Resource, fields
from platzky.config import LanguagesMapping

from goodmap.formatter import prepare_pin


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def paginate_results(items, raw_params, sort_by_default=None):
    """
    Apply pagination and sorting to a list of items.

    Args:
        items: The list of items to paginate
        raw_params: The query parameters dictionary

    Returns:
        Tuple of (paginated_items, pagination_metadata)
    """
    # Extract pagination parameters
    try:
        page = int(raw_params.pop("page", ["1"])[0])
    except ValueError:
        page = 1

    per_page_raw = raw_params.pop("per_page", [None])[0]
    if per_page_raw is None:
        per_page = 20
    elif per_page_raw == "all":
        per_page = None
    else:
        try:
            per_page = max(1, int(per_page_raw))
        except ValueError:
            per_page = 20

    sort_by = raw_params.pop("sort_by", [None])[0] or sort_by_default
    sort_order = raw_params.pop("sort_order", ["asc"])[0].lower()

    def get_sort_key(item):
        if not sort_by:
            return None

        value = None
        if isinstance(item, dict):
            value = item.get(sort_by)
        else:
            value = getattr(item, sort_by, None)

        return (value is not None, value)

    if sort_by:
        reverse = sort_order == "desc"
        items.sort(key=get_sort_key, reverse=reverse)

    # Apply pagination
    total = len(items)
    if per_page:
        start = (page - 1) * per_page
        end = start + per_page
        page_items = items[start:end]
        total_pages = (total + per_page - 1) // per_page
    else:
        page_items = items
        total_pages = 1
        page = 1
        per_page = total

    return page_items, {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def core_pages(
    database, languages: LanguagesMapping, notifier_function, csrf_generator, location_model
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

            # TODO getting visible_data and meta_data should be taken from db methods
            #    e.g. db.get_visible_data() and db.get_meta_data()
            #    visible_data and meta_data should be models
            all_data = database.get_data()
            visible_data = all_data["visible_data"]
            meta_data = all_data["meta_data"]

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
            all_data = database.get_data()
            categories = make_tuple_translation(all_data["categories"].keys())
            return jsonify(categories)

    @core_api.route("/languages")
    class Languages(Resource):
        def get(self):
            """Shows all available languages"""
            return jsonify(languages)

    @core_api.route("/category/<category_type>")
    class CategoryTypes(Resource):
        def get(self, category_type):
            """Shows all available types in category"""
            all_data = database.get_data()
            local_data = make_tuple_translation(all_data["categories"][category_type])
            return jsonify(local_data)

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
            # Raw query params from request
            raw_params = request.args.to_dict(flat=False)
            all_locations = database.get_locations(raw_params)
            page_items, pagination = paginate_results(
                all_locations, raw_params, sort_by_default="name"
            )
            items = [x.model_dump() for x in page_items]
            return jsonify({"items": items, **pagination})

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
            raw_params = request.args.to_dict(flat=False)
            suggestions = database.get_suggestions(raw_params)
            page_items, pagination = paginate_results(suggestions, raw_params)
            return jsonify({"items": page_items, **pagination})

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
            raw_params = request.args.to_dict(flat=False)
            reports = database.get_reports(raw_params)
            page_items, pagination = paginate_results(reports, raw_params)
            return jsonify({"items": page_items, **pagination})

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

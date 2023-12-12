from flask import Blueprint, jsonify, make_response, request
from flask_babel import gettext
from flask_restx import Api, Resource, fields

from goodmap.config import LanguagesMapping

from .core import get_queried_data
from .formatter import prepare_pin


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def core_pages(
    database, languages: LanguagesMapping, notifier_function, csrf_generator
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

    @core_api.route("/report-location")
    class ReportLocation(Resource):
        @core_api.expect(location_report_model)
        def post(self):
            """Report location"""
            try:
                location_report = request.get_json()
                message = (
                    f"A location has been reported: '{location_report['id']}' "
                    f"with problem: {location_report['description']}"
                )
                notifier_function(message)
            except Exception as e:
                return make_response(jsonify({"message": f"Error sending notification : {e}"}), 400)
            return make_response(jsonify({"message": "Location reported"}), 200)

    @core_api.route("/data")
    class Data(Resource):
        def get(self):
            """
            Shows all data filtered by query parameters
            e.g. /api/data?category=category1&category=category2
            """
            all_data = database.get_data()
            query_params = request.args.to_dict(flat=False)
            data = all_data["data"]
            categories = all_data["categories"]
            visible_data = all_data["visible_data"]
            meta_data = all_data["meta_data"]
            queried_data = get_queried_data(data, categories, query_params)
            formatted_data = [prepare_pin(x, visible_data, meta_data) for x in queried_data]
            return jsonify(formatted_data)

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

    return core_api_blueprint

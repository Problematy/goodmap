from flask import Blueprint, jsonify, make_response, request
from flask_babel import gettext
from flask_restx import Api, Resource
from pydantic.tools import parse_obj_as

from goodmap.config import LanguagesMapping

from .core import get_queried_data
from .data_models.location import Location
from .formatter import prepare_pin


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def core_pages(database, languages: LanguagesMapping, notifier_function) -> Blueprint:
    core_api_blueprint = Blueprint("api", __name__, url_prefix="/api")
    core_api = Api(core_api_blueprint, doc="/doc", version="0.1")

    @core_api.route("/report_location")
    class ReportLocation(Resource):
        def post(self):
            """Report location"""
            try:
                location_json = request.get_json()
                location = parse_obj_as(Location, location_json)
                message = (
                    f"A location has been reported: '{location.name}' "
                    f"at coordinates {location.coordinates}"
                )
                notifier_function(message)
            except Exception as e:
                return make_response(jsonify({"message": f"Error sending email: {e}"}), 400)
            return make_response(jsonify({"message": "Location reported"}), 200)

    @core_api.route("/data")
    class Data(Resource):
        def get(self):
            """Shows all data"""
            all_data = database.get_data()
            query_params = request.args.to_dict(flat=False)
            data = all_data["data"]
            categories = all_data["categories"]
            visible_data = all_data["visible_data"]
            queried_data = get_queried_data(data, categories, query_params)
            formatted_data = [prepare_pin(x, visible_data) for x in queried_data]
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

    return core_api_blueprint

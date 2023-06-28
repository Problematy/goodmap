from flask import Blueprint, jsonify, request
from flask_babel import gettext
from flask_expects_json import expects_json
from flask_restx import Api, Resource

from goodmap.config import LanguagesMapping

from .core import get_queried_data
from .formatter import prepare_pin
from .dto_schemas.report_location_schema import report_location_schema


def make_tuple_translation(keys_to_translate):
    return [(x, gettext(x)) for x in keys_to_translate]


def core_pages(database, languages: LanguagesMapping, email_service):
    core_api_blueprint = Blueprint("api", __name__, url_prefix="/api")
    core_api = Api(core_api_blueprint, doc="/doc", version="0.1")

    if email_service:
        @core_api.route("/locations:report", methods=["POST"])
        @expects_json(report_location_schema)
        def report_location():
            request_body = request.get_json()
            email_service.send_report_location_email(request_body)
            return "", 200

    @core_api.route("/data")
    class Data(Resource):
        def get(self):
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
            all_data = database.get_data()
            categories = make_tuple_translation(all_data["categories"].keys())
            return jsonify(categories)

    @core_api.route("/languages")
    class Languages(Resource):
        def get(self):
            return jsonify(languages)

    @core_api.route("/category/<category_type>")
    class CategoryTypes(Resource):
        def get(self, category_type):
            all_data = database.get_data()
            local_data = make_tuple_translation(all_data["categories"][category_type])
            return jsonify(local_data)

    return core_api_blueprint

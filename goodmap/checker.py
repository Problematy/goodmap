from flask import Blueprint, request, abort, Response # render_template,


def checker_page(database):
    blueprint = Blueprint('checker', __name__, url_prefix="/checker")

    #TODO add precheck of data
    def add_entry(data):
        database.save_entry(data)

    # #TODO login check needs to be added
    # @blueprint.route('/entry', methods=["POST"])
    # def add_place_to_database():
    #     if not request.is_json:
    #         abort(404)
    #     else:
    #         data = request.get_json()
    #         add_entry(data)
    #         return Response(status=201)

    return blueprint

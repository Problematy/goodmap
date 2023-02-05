from platzky import platzky

from flask import render_template, redirect, Blueprint
from os import path
from goodmap.services.email_service.email_service import EmailService

from goodmap.db.extend import extend_app_db
from .core_api import core_pages


def create_app(config_path):
    config = platzky.config.from_file(config_path)
    config.add_translations_dir(path.join(path.dirname(__file__), "./translations"))

    app = platzky.create_app_from_config(config)
    extend_app_db(app)
    app.email_service = EmailService(app.config["SMTP"], app.sendmail)

    app.register_blueprint(core_pages(app.db, app.config["LANGUAGES"], app.email_service))
    main = create_app_original(config)
    app.register_blueprint(main)

    return app


def create_app_original(config):
    url_prefix = "/"
    goodmap = Blueprint('goodmap', __name__,
                         url_prefix=url_prefix, template_folder='templates')

    if overwrites := config.asdict().get("ROUTE_OVERWRITES"):
        for source, destination in overwrites.items():
            @goodmap.route(source)
            def testing_map():
                return redirect(destination)

    @goodmap.route("/")
    def index():
        return render_template('map.html')

    return goodmap

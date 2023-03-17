from flask import Flask, request, session, redirect, render_template
from flask_babel import Babel
from flask_minify import Minify

import os
import urllib.parse

from . import config, db_loader
from .blog import blog
from .plugin_loader import plugify
from .seo import seo
from .www_handler import redirect_www_to_nonwww, redirect_nonwww_to_www


def create_app_from_config(config_object):
    engine = create_engine_from_config(config_object)

    blog_blueprint = blog.create_blog_blueprint(db=engine.db,
                                                config=engine.config, babel=engine.babel)
    seo_blueprint = seo.create_seo_blueprint(db=engine.db,
                                             config=engine.config)
    engine.register_blueprint(blog_blueprint)
    engine.register_blueprint(seo_blueprint)
    Minify(app=engine, html=True, js=True, cssless=True)
    return engine


def create_app(config_path):
    absolute_config_path = os.path.join(os.getcwd(), config_path)
    config_object = config.from_file(absolute_config_path)
    return create_app_from_config(config_object)


def create_engine_from_config(config_object):
    config_dict = config_object.asdict()
    db_driver = db_loader.load_db_driver(config_dict["DB"]["TYPE"])
    db = db_driver.get_db(config_dict)
    languages = config_dict["LANGUAGES"]
    domain_langs = config_dict["DOMAIN_TO_LANG"]
    return create_engine(config_dict, db, languages, domain_langs)


def create_engine(config, db, languages, domain_langs):
    app = Flask(__name__)
    app.config.from_mapping(config)

    app.db = db
    app.babel = Babel(app)
    languages = languages
    domain_langs = domain_langs

    @app.before_request
    def handle_www_redirection():
        if app.config["USE_WWW"]:
            return redirect_nonwww_to_www()
        else:
            return redirect_www_to_nonwww()

    @app.babel.localeselector
    def get_locale():
        domain = request.headers['Host']
        lang = domain_langs.get(domain,
                                session.get('language',
                                            request.accept_languages.best_match(languages.keys(), 'en')))
        session['language'] = lang
        return lang

    def get_langs_domain(lang):
        return languages.get(lang).get('domain')

    @app.route('/lang/<string:lang>', methods=["GET"])
    def change_language(lang):
        if new_domain := get_langs_domain(lang):
            return redirect("http://" + new_domain, code=301)
        else:
            session['language'] = lang
            return redirect(request.referrer)

    @app.context_processor
    def utils():
        return {
            "app_name": app.config["APP_NAME"],
            'languages': languages,
            "current_flag": languages[get_locale()]['flag'],
            "current_language": get_locale(),
            "url_link": lambda x: urllib.parse.quote(x, safe=''),
            "menu_items": app.db.get_menu_items()
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html', title='404'), 404

    return plugify(app)

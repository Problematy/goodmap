import typing as t
import urllib.parse

import typing_extensions as te
from flask import Flask, redirect, render_template, request, session
from flask_babel import Babel
from flask_minify import Minify

from goodmap.config import Config, GoogleJsonDbConfig, GraphQlDbConfig, JsonFileDbConfig
from goodmap.platzky.db import google_json_db, graph_ql_db, json_file_db

from .blog import blog
from .plugin_loader import plugify
from .seo import seo
from .www_handler import redirect_nonwww_to_www, redirect_www_to_nonwww


def create_app_from_config(config: Config) -> Flask:
    engine = create_engine_from_config(config)
    blog_blueprint = blog.create_blog_blueprint(
        db=engine.db,  # pyright: ignore
        config=config,
        babel=engine.babel,  # pyright: ignore
    )
    seo_blueprint = seo.create_seo_blueprint(db=engine.db, config=engine.config)  # pyright: ignore
    engine.register_blueprint(blog_blueprint)
    engine.register_blueprint(seo_blueprint)
    Minify(app=engine, html=True, js=True, cssless=True)
    return engine


def create_engine_from_config(config: Config) -> Flask:
    if isinstance(config.db, JsonFileDbConfig):
        db = json_file_db.get_db(config.db)
    elif isinstance(config.db, GoogleJsonDbConfig):
        db = google_json_db.get_db(config.db)
    elif isinstance(config.db, GraphQlDbConfig):  # pyright: ignore[reportUnnecessaryIsInstance]
        db = graph_ql_db.get_db(config.db)
    else:
        te.assert_never(config.db)
    return create_engine(config, db)


def create_engine(config: Config, db) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(config.dict(by_alias=True))
    app.db = db  # pyright: ignore
    app.babel = Babel(app)  # pyright: ignore

    @app.before_request
    def handle_www_redirection():
        if config.use_www:
            return redirect_nonwww_to_www()
        else:
            return redirect_www_to_nonwww()

    @app.babel.localeselector  # pyright: ignore
    def get_locale() -> t.Optional[str]:
        domain = request.headers["Host"]
        lang = config.domain_to_lang.get(domain)
        if lang is None:
            lang = session.get(
                "language", request.accept_languages.best_match(config.languages.keys(), "en")
            )
        session["language"] = lang
        return lang

    def get_langs_domain(lang: str) -> t.Optional[str]:
        lang_cfg = config.languages.get(lang)
        if lang_cfg is None:
            return None
        return lang_cfg.domain

    @app.route("/lang/<string:lang>", methods=["GET"])
    def change_language(lang):
        if new_domain := get_langs_domain(lang):
            return redirect("http://" + new_domain, code=301)
        else:
            session["language"] = lang
            return redirect(request.referrer)

    @app.context_processor
    def utils():
        locale = get_locale()
        flag = ""
        if locale is not None:
            flag = lang.flag if (lang := config.languages.get(locale)) is not None else ""
        return {
            "app_name": config.app_name,
            "languages": config.languages_dict,
            "current_flag": flag,
            "current_language": locale,
            "url_link": lambda x: urllib.parse.quote(x, safe=""),  # pyright: ignore
            "menu_items": app.db.get_menu_items(),  # pyright: ignore
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", title="404"), 404

    return plugify(app, config.plugins)

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
        db=engine.db,
        config=config,
        locale_func=engine.get_locale,
    )
    seo_blueprint = seo.create_seo_blueprint(db=engine.db, config=engine.config)
    engine.register_blueprint(blog_blueprint)
    engine.register_blueprint(seo_blueprint)

    Minify(app=engine, html=True, js=True, cssless=True)
    return engine


class Engine(Flask):
    def __init__(self, config: Config, db, import_name):
        super().__init__(import_name)
        self.config.from_mapping(config.dict(by_alias=True))
        self.db = db

        babel_translation_directories = ";".join(config.translation_directories)

        self.babel = Babel(
            self,
            locale_selector=self.get_locale,
            default_translation_directories=babel_translation_directories,
        )

    def get_locale(self) -> str:
        domain = request.headers["Host"]
        domain_to_lang = self.config.get("DOMAIN_TO_LANG")

        languages = self.config.get("LANGUAGES", {}).keys()
        backup_lang = session.get(
            "language",
            request.accept_languages.best_match(languages, "en"),
        )

        if domain_to_lang:
            lang = domain_to_lang.get(domain, backup_lang)
        else:
            lang = backup_lang

        session["language"] = lang
        return lang


def create_engine(config: Config, db) -> Engine:
    app = Engine(config, db, __name__)

    @app.before_request
    def handle_www_redirection():
        if config.use_www:
            return redirect_nonwww_to_www()
        else:
            return redirect_www_to_nonwww()

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
        locale = app.get_locale()
        flag = lang.flag if (lang := config.languages.get(locale)) is not None else ""
        return {
            "app_name": config.app_name,
            "languages": config.languages_dict,
            "current_flag": flag,
            "current_language": locale,
            "url_link": lambda x: urllib.parse.quote(x, safe=""),  # pyright: ignore
            "menu_items": app.db.get_menu_items(),
        }

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", title="404"), 404

    return plugify(app, config.plugins)


def create_engine_from_config(config: Config) -> Engine:
    if isinstance(config.db, JsonFileDbConfig):
        db = json_file_db.get_db(config.db)
    elif isinstance(config.db, GoogleJsonDbConfig):
        db = google_json_db.get_db(config.db)
    elif isinstance(config.db, GraphQlDbConfig):  # pyright: ignore[reportUnnecessaryIsInstance]
        db = graph_ql_db.get_db(config.db)
    else:
        te.assert_never(config.db)
    return create_engine(config, db)

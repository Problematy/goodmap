import typing as t
import urllib.parse
from os.path import dirname

from flask import Blueprint, current_app, make_response, render_template, request


def create_seo_blueprint(db, config: dict[str, t.Any]):
    seo = Blueprint(
        "seo",
        __name__,
        url_prefix=config["SEO_PREFIX"],
        template_folder=f"{dirname(__file__)}/../templates",
    )

    @seo.route("/robots.txt")
    def robots():
        robots_response = render_template("robots.txt", domain=request.host, mimetype="text/plain")
        response = make_response(robots_response)
        response.headers["Content-Type"] = "text/plain"
        return response

    @seo.route("/sitemap.xml")
    def main_sitemap():
        if domain_to_lang := config["DOMAIN_TO_LANG"]:
            return sitemap(domain_to_lang[request.host])
        else:
            return sitemap(
                config.get("TRANSLATION_DIRECTORIES")
            )  # TODO should be based on localization not on config

    def sitemap(lang):
        """
        Route to dynamically generate a sitemap of your website/application.
        lastmod and priority tags omitted on static pages.
        lastmod included on dynamic content such as seo posts.
        """

        global url
        host_components = urllib.parse.urlparse(request.host_url)
        host_base = host_components.scheme + "://" + host_components.netloc

        # Static routes with static content
        static_urls = list()
        for rule in current_app.url_map.iter_rules():
            if not str(rule).startswith("/admin") and not str(rule).startswith("/user"):
                if rule.methods is not None and "GET" in rule.methods and len(rule.arguments) == 0:
                    url = {"loc": f"{host_base}{str(rule)}"}
                    static_urls.append(url)

        # Dynamic routes with dynamic content
        dynamic_urls = list()
        seo_posts = db.get_all_posts(lang)
        for post in seo_posts:
            slug = post["slug"]
            datet = post["date"].split("T")[0]
            url = {"loc": f"{host_base}/{slug}", "lastmod": datet}
            dynamic_urls.append(url)

        statics = list({v["loc"]: v for v in static_urls}.values())
        dynamics = list({v["loc"]: v for v in dynamic_urls}.values())
        xml_sitemap = render_template(
            "sitemap.xml",
            static_urls=statics,
            dynamic_urls=dynamics,
            host_base=host_base,
        )
        response = make_response(xml_sitemap)
        response.headers["Content-Type"] = "application/xml"
        return response

    return seo

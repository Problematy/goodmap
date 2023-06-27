from os.path import dirname

from flask import Blueprint, make_response, render_template, request
from markupsafe import Markup

from goodmap.config import Config
from goodmap.platzky.blog import comment_form, post_formatter


def create_blog_blueprint(db, config: Config, locale_func):
    url_prefix = config.blog_prefix
    blog = Blueprint(
        "blog",
        __name__,
        url_prefix=url_prefix,
        template_folder=f"{dirname(__file__)}/../templates",
    )

    @blog.app_template_filter()
    def markdown(text):
        return Markup(text)

    @blog.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", title="404"), 404

    @blog.route("/", methods=["GET"])
    def index():
        lang = locale_func()
        return render_template("blog.html", posts=db.get_all_posts(lang))

    @blog.route("/feed", methods=["GET"])
    def get_feed():
        lang = locale_func()
        response = make_response(render_template("feed.xml", posts=db.get_all_posts(lang)))
        response.headers["Content-Type"] = "application/xml"
        return response

    @blog.route("/<post_slug>", methods=["POST"])
    def post_comment(post_slug):
        comment = request.form.to_dict()
        db.add_comment(
            post_slug=post_slug,
            author_name=comment["author_name"],
            comment=comment["comment"],
        )
        return get_post(post_slug=post_slug)

    @blog.route("/<post_slug>", methods=["GET"])
    def get_post(post_slug):
        if raw_post := db.get_post(post_slug):
            formatted_post = post_formatter.format_post(raw_post)
            return render_template(
                "post.html",
                post=formatted_post,
                post_slug=post_slug,
                form=comment_form.CommentForm(),
                comment_sent=request.args.get("comment_sent"),
            )
        else:
            return page_not_found("no such page")

    @blog.route("/page/<path:page_slug>", methods=["GET"])
    def get_page(
        page_slug,
    ):  # TODO refactor to share code with get_post since they are very similar
        if page := db.get_page(page_slug):
            if cover_image := page.get("coverImage"):
                cover_image_url = cover_image["url"]
            else:
                cover_image_url = None
            return render_template("page.html", page=page, cover_image=cover_image_url)
        else:
            return page_not_found("no such page")

    @blog.route("/tag/<path:tag>", methods=["GET"])
    def get_posts_from_tag(tag):
        lang = locale_func()
        posts = db.get_posts_by_tag(tag, lang)
        return render_template("blog.html", posts=posts, subtitle=f" - tag: {tag}")

    return blog

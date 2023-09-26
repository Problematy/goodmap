import datetime

from pydantic import Field

from goodmap.platzky.blog.db import DB, DBConfig


class JsonDbConfig(DBConfig):
    data: dict = Field(alias="DATA")  # type: ignore


def get_db(config):
    json_db_config = JsonDbConfig.parse_obj(config)
    return Json(json_db_config.data)


class Json(DB):
    def __init__(self, data_dict):
        self.data = data_dict

    def get_all_posts(self, lang):
        return [post for post in self.data.get("posts", ()) if post["language"] == lang]

    def get_post(self, slug):
        return next(post for post in self.data.get("posts") if post["slug"] == slug)

    # TODO: add test for non-existing page
    def get_page(self, slug):
        return next(
            (page for page in self.data.get("site_content").get("pages") if page["slug"] == slug),
            None,
        )

    def get_menu_items(self):
        post = self.data.get("site_content").get("menu_items", [])
        return post

    def get_posts_by_tag(self, tag, lang):
        return (post for post in self.data["posts"] if tag in post["tags"])

    def get_all_providers(self):
        return self.data["providers"]

    def get_all_questions(self):
        return self.data["questions"]

    def get_logo_url(self):
        return self.data.get("site_content").get("logo_url", "")

    def get_font(self):
        return self.data.get("site_content").get("font", "")

    def get_primary_color(self):
        return self.data.get("site_content").get("primary_color", "white")

    def get_secondary_color(self):
        return self.data.get("site_content").get("secondary_color", "navy")

    def add_comment(self, author_name, comment, post_slug):
        comment = {
            "author": str(author_name),
            "comment": str(comment),
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        post_index = next(
            i for i in range(len(self.data["posts"])) if self.data["posts"][i]["slug"] == post_slug
        )
        self.data["posts"][post_index]["comments"].append(comment)

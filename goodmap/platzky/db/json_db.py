import datetime

from goodmap.platzky.blog.db import DB


class Json(DB):
    def __init__(self, data_dict):
        self.data = data_dict

    def get_all_posts(self, lang):
        return [post for post in self.data.get("posts", ()) if post["language"] == lang]

    def get_post(self, slug):
        return next(post for post in self.data.get("posts") if post["slug"] == slug)

    # TODO: add test for non-existing page
    def get_page(self, slug):
        return next((page for page in self.data.get("pages") if page["slug"] == slug), None)

    def get_menu_items(self):
        post = self.data.get("menu_items", [])
        return post

    def get_posts_by_tag(self, tag, lang):
        return (post for post in self.data["posts"] if tag in post["tags"])

    def get_all_providers(self):
        return self.data["providers"]

    def get_all_questions(self):
        return self.data["questions"]

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

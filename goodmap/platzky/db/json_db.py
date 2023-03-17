from goodmap.platzky.blog.db import DB
import datetime


def get_db(config):
    return Json(config["DATA"])


class Json(DB):
    def __init__(self, data_dict):
        self.data = data_dict

    def get_all_posts(self, lang):
        posts = (filter(lambda x: x["language"] == lang, self.data.get("posts", [])))
        return list(posts)

    def get_post(self, slug):
        post = next(filter(lambda x: x["slug"] == slug, self.data["posts"]), None)
        return post

    def get_page(self, slug):
        post = next(filter(lambda x: x["slug"] == slug, self.data["pages"]), None)
        return post

    def get_menu_items(self):
        post = self.data.get("menu_items", [])
        return post

    def get_posts_by_tag(self, tag, lang):
        posts = filter(lambda x: tag in x["tags"], self.data["posts"])
        return posts

    def get_all_providers(self):
        return self.data["providers"]

    def get_all_questions(self):
        return self.data["questions"]

    def add_comment(self, author_name, comment, post_slug):
        comment = {
            "author": str(author_name),
            "comment": str(comment),
            "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        }
        post_index = next(i for i in range(len(self.data["posts"])) if self.data["posts"][i]["slug"] == post_slug)
        self.data["posts"][post_index]["comments"].append(comment)

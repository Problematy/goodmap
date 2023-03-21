from typing import Any


class DB:
    def get_all_posts(self, lang) -> Any:
        pass

    def get_post(self, slug):
        pass

    def get_page(self, slug):
        pass

    def get_posts_by_tag(self, tag, lang) -> Any:
        pass

    def get_menu(self):
        pass

    def add_comment(self, author_name, comment, post_slug):
        pass

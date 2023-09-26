from typing import Any

from pydantic import BaseModel, Extra, Field


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


class DBConfig(BaseModel, extra=Extra.forbid, allow_mutation=False):
    type_: str = Field(alias="TYPE")

from typing import Any

from pydantic import BaseModel, Extra, Field
from functools import partial


class DB:
    def extend(self, function_name, function):
        """
        Add a function to the DB object. The function must take the DB object as first parameter.
        """
        bound = partial(function, self)
        setattr(self, function_name, bound)

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

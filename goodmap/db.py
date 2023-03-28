import json
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

import typing_extensions as te
from google.cloud import storage

from goodmap.config import DatabaseConfig, GoogleJsonDbConfig, JsonFileDbConfig


class MenuItem(t.TypedDict):
    name: str
    url: str


class Post(t.TypedDict):
    language: str
    slug: str
    tags: tuple[str, ...]


class Page(t.TypedDict):
    slug: str


class MapData(t.TypedDict):
    name: str
    position: tuple[float, float]
    accessible_by: tuple[str, ...]


class Map(t.TypedDict):
    data: tuple[MapData, ...]
    categories: dict[str, tuple[str, ...]]
    visible_data: tuple[str, ...]


class DatabaseData(t.TypedDict):
    menu_items: tuple[MenuItem, ...]
    posts: tuple[Post, ...]
    pages: tuple[Page, ...]
    map: Map


class Database(ABC):
    @abstractmethod
    def get_all_posts(self, lang: str) -> t.Any:
        pass

    @abstractmethod
    def get_post(self, slug: str) -> Post:
        pass

    @abstractmethod
    def get_page(self, slug: str) -> Page:
        pass

    @abstractmethod
    def get_posts_by_tag(self, tag: str, lang: str) -> tuple[Post, ...]:
        pass

    @abstractmethod
    def get_menu_items(self) -> tuple[MenuItem, ...]:
        pass

    @abstractmethod
    def get_map(self) -> Map:
        ...


@dataclass
class JsonDatabase(Database):
    data: DatabaseData

    @classmethod
    def from_json(cls, path: str) -> "JsonDatabase":
        with open(path) as f:
            data = json.load(f)
        return cls(data)

    @classmethod
    def from_google_bucket_json(cls, bucket_name: str, source_blob_name: str) -> "JsonDatabase":
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(source_blob_name)
        raw_data = blob.download_as_text(client=None)
        data = json.loads(raw_data)
        return cls(data)

    @classmethod
    def from_config(cls, config: DatabaseConfig) -> "JsonDatabase":
        if isinstance(config, JsonFileDbConfig):
            return cls.from_json(config.path)
        elif isinstance(config, GoogleJsonDbConfig):  # pyright: ignore[reportUnnecessaryIsInstance]
            return cls.from_google_bucket_json(config.bucket_name, config.source_blob_name)
        else:
            te.assert_never(config)

    def get_all_posts(self, lang: str) -> tuple[Post, ...]:
        return tuple(post for post in self.data["posts"] if post["language"] == lang)

    def get_post(self, slug: str) -> Post:
        return next(post for post in self.data["posts"] if post["slug"] == slug)

    def get_page(self, slug: str) -> Page:
        return next(page for page in self.data["pages"] if page["slug"] == slug)

    def get_posts_by_tag(self, tag: str, lang: str) -> tuple[Post, ...]:
        return tuple(post for post in self.data["posts"] if tag in post["tags"])

    def get_menu_items(self) -> tuple[MenuItem, ...]:
        return self.data["menu_items"]

    def get_map(self) -> Map:
        return self.data["map"]

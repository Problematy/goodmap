import typing as t

import yaml
from pydantic import BaseModel, Field

from .db.db import DBConfig
from .db.db_loader import get_db_module


class StrictBaseModel(BaseModel):
    class Config:
        allow_mutation = False


class LanguageConfig(StrictBaseModel):
    name: str = Field(alias="name")
    flag: str = Field(alias="flag")
    domain: t.Optional[str] = Field(default=None, alias="domain")


Languages = dict[str, LanguageConfig]
LanguagesMapping = t.Mapping[str, t.Mapping[str, str]]


def languages_dict(languages: Languages) -> LanguagesMapping:
    return {name: lang.dict() for name, lang in languages.items()}


class Config(StrictBaseModel):
    app_name: str = Field(alias="APP_NAME")
    secret_key: str = Field(alias="SECRET_KEY")
    db: DBConfig = Field(alias="DB")
    use_www: bool = Field(default=True, alias="USE_WWW")
    seo_prefix: str = Field(default="/", alias="SEO_PREFIX")
    blog_prefix: str = Field(default="/", alias="BLOG_PREFIX")
    languages: Languages = Field(default_factory=dict, alias="LANGUAGES")
    domain_to_lang: dict[str, str] = Field(default_factory=dict, alias="DOMAIN_TO_LANG")
    plugins: dict[str, dict[str, str]] = Field(default_factory=dict, alias="PLUGINS")
    translation_directories: list[str] = Field(
        default_factory=list,
        alias="TRANSLATION_DIRECTORIES",
    )
    debug: bool = Field(default=False, alias="DEBUG")
    testing: bool = Field(default=False, alias="TESTING")

    @classmethod
    def parse_obj(cls, obj: t.Any):
        db_cfg_type = get_db_module(obj["DB"]["TYPE"]).db_config_type()
        obj["DB"] = db_cfg_type.parse_obj(obj["DB"])
        return super().parse_obj(obj)

    @classmethod
    def parse_yaml(cls, path: str) -> "Config":
        with open(path) as f:
            cfg = yaml.safe_load(f)
        return cls.parse_obj(cfg)

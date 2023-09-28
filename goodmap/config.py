import typing as t

import yaml
from pydantic import BaseModel, Extra, Field


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
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
    db: dict = Field(alias="DB")  # pyright: ignore
    use_www: bool = Field(default=True, alias="USE_WWW")
    seo_prefix: str = Field(default="/", alias="SEO_PREFIX")
    blog_prefix: str = Field(default="/", alias="BLOG_PREFIX")
    languages: Languages = Field(default_factory=dict, alias="LANGUAGES")
    domain_to_lang: dict[str, str] = Field(default_factory=dict, alias="DOMAIN_TO_LANG")
    plugins: dict[str, dict[str, str]] = Field(default_factory=dict, alias="PLUGINS")
    route_overwrites: dict[str, str] = Field(default_factory=dict, alias="ROUTE_OVERWRITES")
    translation_directories: list[str] = Field(
        default_factory=list,
        alias="TRANSLATION_DIRECTORIES",
    )
    debug: bool = Field(default=False, alias="DEBUG")
    testing: bool = Field(default=False, alias="TESTING")

    @classmethod
    def parse_yaml(cls, path: str) -> "Config":
        with open(path) as f:
            cfg = yaml.safe_load(f)
        return cls.parse_obj(cfg)

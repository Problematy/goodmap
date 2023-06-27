import typing as t

import yaml
from pydantic import BaseModel, Extra, Field


class StrictBaseModel(BaseModel):
    class Config:
        extra = Extra.forbid
        allow_mutation = False


class JsonFileDbConfig(StrictBaseModel):
    type_: t.Literal["json_file"] = Field(alias="TYPE")
    path: str = Field(alias="PATH")


class GoogleJsonDbConfig(StrictBaseModel):
    type_: t.Literal["google_json"] = Field(alias="TYPE")
    bucket_name: str = Field(alias="BUCKET_NAME")
    source_blob_name: str = Field(alias="SOURCE_BLOB_NAME")


class GraphQlDbConfig(StrictBaseModel):
    type_: t.Literal["graph_ql"] = Field(alias="TYPE")
    endpoint: str = Field(alias="CMS_ENDPOINT")
    token: str = Field(alias="CMS_TOKEN")


class LanguageConfig(StrictBaseModel):
    name: str = Field(alias="name")
    flag: str = Field(alias="flag")
    domain: t.Optional[str] = Field(default=None, alias="domain")


Languages = dict[str, LanguageConfig]
LanguagesMapping = t.Mapping[str, t.Mapping[str, str]]


class Smtp(StrictBaseModel):
    port: str = Field(alias="PORT")
    server: str = Field(alias="SERVER")
    address: str = Field(alias="ADDRESS")
    password: str = Field(alias="PASSWORD")
    domain: t.Optional[str] = Field(default=None, alias="domain")


class Config(StrictBaseModel):
    app_name: str = Field(alias="APP_NAME")
    secret_key: str = Field(alias="SECRET_KEY")
    db: t.Union[JsonFileDbConfig, GoogleJsonDbConfig, GraphQlDbConfig] = Field(alias="DB")
    use_www: bool = Field(default=True, alias="USE_WWW")
    seo_prefix: str = Field(default="/", alias="SEO_PREFIX")
    blog_prefix: str = Field(default="/", alias="BLOG_PREFIX")
    smtp: Smtp = Field(default_factory=dict, alias="SMTP")
    languages: Languages = Field(default_factory=dict, alias="LANGUAGES")
    domain_to_lang: dict[str, str] = Field(default_factory=dict, alias="DOMAIN_TO_LANG")
    plugins: set[t.Any] = Field(default_factory=set, alias="PLUGINS")
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

    @property
    def languages_dict(self) -> LanguagesMapping:
        return {name: lang.dict() for name, lang in self.languages.items()}

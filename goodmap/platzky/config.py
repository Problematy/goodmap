import os.path
import yaml


def is_db_ok(mapping):
    if 'DB' not in mapping:
        raise Exception("DB not set")
    if 'TYPE' not in mapping['DB']:
        raise Exception("DB type is not set")
    if mapping['DB']['TYPE'] not in ['graph_ql', 'json_file', 'google_json']:
        raise Exception("DB type is not supported")
    return True


class Config():
    def __init__(self, mapping):
        if is_db_ok(mapping):
            self.config = mapping
        else:
            raise Exception("Config is wrong")

    def add_translations_dir(self, absolute_translation_dir):
        self.config["BABEL_TRANSLATION_DIRECTORIES"] += ";" + absolute_translation_dir

    def asdict(self):
        return self.config


def get_config_mapping(base_config):
    default_config = {  # TODO move it to platzky
        "USE_WWW": True,
        "SEO_PREFIX": "/",
        "BLOG_PREFIX": "/",
        "LANGUAGES": {},
        "DOMAIN_TO_LANG": {},
        "PLUGINS": []
    }

    config = default_config | base_config
    babel_format_dir = ";".join(config.get("TRANSLATION_DIRECTORIES", []))
    config["BABEL_TRANSLATION_DIRECTORIES"] = babel_format_dir
    return config


def from_file(absolute_config_path):
    with open(absolute_config_path, "r") as stream:
        file_config = yaml.safe_load(stream)
    file_config["CONFIG_PATH"] = absolute_config_path
    config_from_file = from_mapping(file_config)
    config_directory = os.path.dirname(absolute_config_path)
    for x in ["locales", "locale", "translations"]:
        translation_directory = os.path.join(config_directory, x)
        config_from_file.add_translations_dir(translation_directory)

    path_to_module_locale = os.path.join(os.path.dirname(__file__), "./locale")
    config_from_file.add_translations_dir(path_to_module_locale)

    return config_from_file


def from_mapping(mapping):
    config_dict = get_config_mapping(mapping)
    return Config(config_dict)

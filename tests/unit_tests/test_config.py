from goodmap.config import Config, languages_dict


def test_parse_template_config() -> None:
    """Test that the template config can be parsed."""
    config = Config.parse_yaml("config-template.yml")
    langs_dict = languages_dict(config.languages)

    wanted_dict = {
        "en": {"domain": None, "flag": "uk", "name": "English"},
        "pl": {"domain": None, "flag": "pl", "name": "polski"},
    }
    assert langs_dict == wanted_dict

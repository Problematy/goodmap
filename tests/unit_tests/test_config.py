from goodmap.config import Config


def test_parse_template_config() -> None:
    """Test that the template config can be parsed."""
    Config.parse_yaml("config-template.yml")

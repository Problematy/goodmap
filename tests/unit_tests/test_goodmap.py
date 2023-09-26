from goodmap import goodmap
from goodmap.config import Config

config = Config(
    APP_NAME="test",
    SECRET_KEY="test",
    DB={"TYPE": "json", "DATA": ""},
)


def test_create_app():
    goodmap.create_app_from_config(config)

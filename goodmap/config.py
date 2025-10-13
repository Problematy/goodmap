import typing as t

import yaml
from platzky.config import Config as PlatzkyConfig
from pydantic import Field


class GoodmapConfig(PlatzkyConfig):
    """Extended configuration for Goodmap with additional frontend library URL."""

    goodmap_frontend_lib_url: str = Field(
        default="https://cdn.jsdelivr.net/npm/@problematy/goodmap@latest",
        alias="GOODMAP_FRONTEND_LIB_URL",
    )

    @classmethod
    def parse_yaml(cls, path: str) -> "GoodmapConfig":
        """Parse YAML configuration file and return GoodmapConfig instance."""
        try:
            with open(path, "r") as f:
                return cls.model_validate(yaml.safe_load(f))
        except FileNotFoundError:
            import sys

            print(f"Config file not found: {path}", file=sys.stderr)
            raise SystemExit(1)

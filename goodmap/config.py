import sys
import typing as t

import yaml
from platzky.config import Config as PlatzkyConfig
from pydantic import Field


class GoodmapConfig(PlatzkyConfig):
    """Extended configuration for Goodmap with additional frontend library URL."""

    goodmap_frontend_lib_url: str = Field(
        default="https://cdn.jsdelivr.net/npm/@problematy/goodmap@0.4.2",
        alias="GOODMAP_FRONTEND_LIB_URL",
    )

    @classmethod
    def model_validate(
        cls,
        obj: t.Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, t.Any] | None = None,
    ) -> "GoodmapConfig":
        """Override to return correct type for GoodmapConfig."""
        return t.cast(
            "GoodmapConfig",
            super().model_validate(
                obj, strict=strict, from_attributes=from_attributes, context=context
            ),
        )

    @classmethod
    def parse_yaml(cls, path: str) -> "GoodmapConfig":
        """Parse YAML configuration file and return GoodmapConfig instance."""
        try:
            with open(path, "r") as f:
                return cls.model_validate(yaml.safe_load(f))
        except FileNotFoundError:
            print(f"Config file not found: {path}", file=sys.stderr)
            raise SystemExit(1)

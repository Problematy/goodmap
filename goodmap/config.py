import sys
import typing as t
from typing import Literal

import yaml
from platzky.config import AttachmentConfig
from platzky.config import Config as PlatzkyConfig
from pydantic import Field


def _default_photo_attachment_config() -> AttachmentConfig:
    """JPEG-only, 5 MiB: goodmap's only current use of attachments is location
    suggestion photos, which the frontend always previews as an <img> and
    auto-compresses to JPEG when oversized - platzky's own AttachmentConfig default
    (PDFs, archives, audio/video, up to 10MB) isn't a safe default for that. Kept as
    goodmap's own default for the inherited `attachment` field below, rather than
    platzky's, so deployments that don't set ATTACHMENT: keep this behavior; those
    that do set it get exactly what they configured.
    """
    return AttachmentConfig(
        allowed_mime_types=frozenset({"image/jpeg"}),
        allowed_extensions=frozenset({"jpg", "jpeg"}),
        max_size=5 * 1024 * 1024,
    )


class GoodmapConfig(PlatzkyConfig):
    """Extended configuration for Goodmap with additional frontend library URL."""

    # Defaults to the frontend bundle shipped in the package and served by the
    # goodmap_frontend blueprint (static_url_path="/static/frontend"). Override
    # with an external URL (e.g. a CDN) when not serving the bundled build.
    goodmap_frontend_lib_url: str = Field(
        default="/static/frontend/index.min.js",
        alias="GOODMAP_FRONTEND_LIB_URL",
    )

    # Overrides platzky's own AttachmentConfig default - see
    # _default_photo_attachment_config for why. Deployments can still set their own
    # allowed formats/size via ATTACHMENT: in YAML, same as any platzky app.
    attachment: AttachmentConfig = Field(
        default_factory=_default_photo_attachment_config,
        alias="ATTACHMENT",
    )

    @classmethod
    def model_validate(
        cls,
        obj: t.Any,
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, t.Any] | None = None,
        by_alias: bool | None = None,
        by_name: bool | None = None,
        extra: Literal["allow", "ignore", "forbid"] | None = None,
    ) -> "GoodmapConfig":
        """Override to return correct type for GoodmapConfig."""
        return t.cast(
            "GoodmapConfig",
            super().model_validate(
                obj,
                strict=strict,
                from_attributes=from_attributes,
                context=context,
                by_alias=by_alias,
                by_name=by_name,
                extra=extra,
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

"""Normalized contracts consumed by Output handling."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class NormalizedOutput:
    """Effective Output policy with Configuration/runtime precedence resolved."""

    path: Path
    generated: bool
    overwrite: bool
    prefix: str | None
    suffix: str | None
    sequence: int | None
    archive_mtime: datetime | None


@dataclass(frozen=True)
class ArchivePresentation:
    """Rendering metadata for human-readable archive output."""

    about_description: str | None
    description_no_targets: str | None
    description_no_always: str | None
    description_empty: str | None
    layout_descriptions: Mapping[str, str | None]
    show_source_paths: bool

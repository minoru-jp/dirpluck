"""Normalized contracts consumed by Output handling."""

from __future__ import annotations

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
    show_source_paths: bool

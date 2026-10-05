"""Rendered archive plan and preview-status models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ._archive_payload import ArchivePayload
from ._extraction_models import EmptySelectionStatus, MissingSelectionStatus


@dataclass(frozen=True)
class ArchivePlan:
    """Rendered ZIP payload plus human-facing preview and diagnostic status."""

    payload: ArchivePayload
    missing: tuple[str, ...] = ()
    optional_missing: tuple[str, ...] = ()
    empty_selections: tuple[EmptySelectionStatus, ...] = ()
    missing_selections: tuple[MissingSelectionStatus, ...] = ()
    diagnostics: tuple[str, ...] = ()
    skipped_link_count: int = 0

    @property
    def entries(self) -> Mapping[str, Path]:
        """Return the rendered archive file entries."""

        return self.payload.entries

    @property
    def readme(self) -> str:
        """Return the generated archive README."""

        return self.payload.readme

    @property
    def empty_directories(self) -> tuple[str, ...]:
        """Return explicit empty directories written to the archive."""

        return self.payload.empty_directories

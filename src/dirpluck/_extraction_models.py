"""Semantic models produced by filesystem extraction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ._target_models import TargetEntryKind


@dataclass(frozen=True)
class EmptySelectionStatus:
    """One source that selected no files during extraction."""

    key: str
    label: str
    archive_root: str
    allow_empty: bool


@dataclass(frozen=True)
class MissingSelectionStatus:
    """One non-path Selection expression that did not match during extraction."""

    source_label: str
    archive_root: str
    expression: str
    optional: bool


@dataclass(frozen=True)
class SelectionTypeMismatchStatus:
    """One Selection entry whose declared file/directory kind did not match."""

    source_label: str
    pattern: str
    expected_kind: TargetEntryKind
    actual_names: tuple[str, ...]
    optional: bool


@dataclass(frozen=True)
class TargetOverlapStatus:
    """One Target that selected files also selected by another source."""

    archive_root: str
    source_kind: TargetEntryKind
    count: int


@dataclass(frozen=True)
class ExtractedSource:
    """Output-relevant summary of one source after filesystem extraction."""

    key: str
    role: Literal["target", "fixed"]
    archive_root: str
    source_kind: TargetEntryKind
    source_path: Path
    description: str | None
    selected_count: int
    layout_name: str | None = None
    scope_name: str | None = None
    scope_description: str | None = None
    target_overlaps: tuple[TargetOverlapStatus, ...] = ()


@dataclass(frozen=True)
class ExtractionResult:
    """Semantic extraction result before any human-readable output is rendered."""

    sources: tuple[ExtractedSource, ...]
    entries: Mapping[str, Path]
    missing: tuple[str, ...] = ()
    optional_missing: tuple[str, ...] = ()
    empty_directories: tuple[str, ...] = ()
    empty_selections: tuple[EmptySelectionStatus, ...] = ()
    missing_selections: tuple[MissingSelectionStatus, ...] = ()
    type_mismatches: tuple[SelectionTypeMismatchStatus, ...] = ()
    skipped_link_count: int = 0

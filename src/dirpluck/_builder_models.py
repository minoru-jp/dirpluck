"""Shared data models for the archive builder pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from .config import Always, Config, Namespace, Pluck, Scope, Selection, SharedPatterns


@dataclass(frozen=True)
class BuildRequest:
    """One build request with Target references and runtime archive options."""

    directories: tuple[str, ...] = ()
    case: str | None = None
    sequence: int | None = None
    paths: bool = False
    archive_mtime: datetime | None = None

    @classmethod
    def create(
        cls,
        *directories: str | Path,
        case: str | None = None,
        sequence: int | None = None,
        paths: bool = False,
        archive_mtime: datetime | None = None,
    ) -> "BuildRequest":
        return cls(
            directories=tuple(
                directory.as_posix() if isinstance(directory, Path) else str(directory)
                for directory in directories
            ),
            case=case,
            sequence=sequence,
            paths=paths,
            archive_mtime=archive_mtime,
        )


@dataclass(frozen=True)
class ResolvedSource:
    """A configured Target or Always source resolved to one concrete directory."""

    key: str
    kind: str
    name: str | None
    description: str | None
    directory: Path
    source_root: str
    namespace: str | None
    archive_root: str
    selection: Selection

    @property
    def label(self) -> str:
        if self.kind == "target":
            return "target" if self.name is None else f"target {self.name!r}"
        return f"always source {self.name!r}"


@dataclass(frozen=True)
class SelectionResult:
    """Files selected for one source plus unmatched patterns and skipped link-like entries."""

    files: tuple[Path, ...]
    missing: tuple[str, ...]
    optional_missing: tuple[str, ...]
    skipped_links: tuple[Path, ...] = ()


@dataclass(frozen=True)
class EmptySelectionStatus:
    """One source that selected no files during archive planning."""

    key: str
    label: str
    archive_root: str
    allow_empty: bool


@dataclass(frozen=True)
class ArchivePlan:
    """Exact archive entries, generated README, and preview-only status details."""

    entries: Mapping[str, Path]
    readme: str
    missing: tuple[str, ...] = ()
    optional_missing: tuple[str, ...] = ()
    empty_directories: tuple[str, ...] = ()
    empty_selections: tuple[EmptySelectionStatus, ...] = ()
    skipped_link_count: int = 0


@dataclass(frozen=True)
class _ConfigurationLayer:
    """One loaded Configuration in the root-to-base linear chain."""

    config: Config


@dataclass(frozen=True)
class _PluckBinding:
    pluck: Pluck
    layer: _ConfigurationLayer


@dataclass(frozen=True)
class _ScopeBinding:
    scope: Scope
    layer: _ConfigurationLayer


@dataclass(frozen=True)
class _AlwaysBinding:
    source: Always
    layer: _ConfigurationLayer


@dataclass(frozen=True)
class _EffectiveConfiguration:
    root: Config
    layers: tuple[_ConfigurationLayer, ...]
    about_description: str | None
    shared: SharedPatterns
    pluck: _PluckBinding | None
    scopes: Mapping[str | None, _ScopeBinding]
    always: Mapping[str, _AlwaysBinding]
    namespaces: Mapping[str, Namespace]


@dataclass(frozen=True)
class _IncludeMatchResult:
    entries: tuple[Path, ...]
    skipped_links: tuple[Path, ...]
    unsupported_entries: tuple[Path, ...]


@dataclass(frozen=True)
class _CollectedFiles:
    files: tuple[Path, ...]
    skipped_links: tuple[Path, ...]

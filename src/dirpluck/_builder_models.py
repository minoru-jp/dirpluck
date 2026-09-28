"""Shared data models for the archive builder pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

from .config import Always, Config, Namespace, Pluck, Scope, Selection, SharedPatterns


@dataclass(frozen=True)
class RuntimeOutput:
    """One runtime-selected exact output path or generated-name directory."""

    path: Path
    generated: bool


@dataclass(frozen=True)
class BuildRequest:
    """One build request with Target references and runtime archive options."""

    directories: tuple[str, ...] = ()
    case: str | None = None
    sequence: int | None = None
    paths: bool = False
    archive_mtime: datetime | None = None
    output: RuntimeOutput | None = None
    force: bool = False

    @classmethod
    def create(
        cls,
        *directories: str | Path,
        case: str | None = None,
        sequence: int | None = None,
        paths: bool = False,
        archive_mtime: datetime | None = None,
        output: RuntimeOutput | None = None,
        force: bool = False,
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
            output=output,
            force=force,
        )


@dataclass(frozen=True)
class ResolvedSource:
    """A configured Target or Always source resolved to one concrete filesystem source."""

    key: str
    kind: str
    name: str | None
    description: str | None
    scope_description: str | None
    source_kind: str
    directory: Path
    source_root: str
    namespace: str | None
    archive_root: str
    selection: Selection | None

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
    opaque_missing: tuple[str, ...] = ()
    opaque_optional_missing: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class EmptySelectionStatus:
    """One source that selected no files during archive planning."""

    key: str
    label: str
    archive_root: str
    allow_empty: bool


@dataclass(frozen=True)
class MissingSelectionStatus:
    """One non-path Selection expression that did not match during planning."""

    source_label: str
    archive_root: str
    expression: str
    optional: bool


@dataclass(frozen=True)
class ArchivePlan:
    """Exact archive entries, generated README, and preview-only status details."""

    entries: Mapping[str, Path]
    readme: str
    missing: tuple[str, ...] = ()
    optional_missing: tuple[str, ...] = ()
    empty_directories: tuple[str, ...] = ()
    empty_selections: tuple[EmptySelectionStatus, ...] = ()
    missing_selections: tuple[MissingSelectionStatus, ...] = ()
    diagnostics: tuple[str, ...] = ()
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
    wrong_type_entries: tuple[Path, ...] = ()


@dataclass(frozen=True)
class _CollectedFiles:
    files: tuple[Path, ...]
    skipped_links: tuple[Path, ...]

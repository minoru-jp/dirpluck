"""Configuration data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

@dataclass(frozen=True)
class ExclusionPattern:
    """One simple case-sensitive name filter for selected source contents.

    ``directory`` is true only when the spelling explicitly ends in ``/``.
    A false value is intentionally broad for ignore semantics and may match
    either a file or a directory name.
    """

    raw: str
    value: str
    match: str
    directory: bool

@dataclass(frozen=True)
class PathExclusion:
    """One concrete Selection-root-relative path excluded from one source tree.

    ``directory`` is true only when the spelling explicitly ends in ``/``.
    Without that marker the concrete ignore is intentionally broad and may
    refer to either an existing file or directory.
    """

    raw: str
    path: str
    directory: bool

@dataclass(frozen=True)
class TargetIgnorePattern:
    """One simple case-sensitive direct-child Target exclusion filter.

    ``directory`` is true only when the spelling explicitly ends in ``/``.
    Without that marker the filter intentionally applies to both file and
    directory Targets.
    """

    raw: str
    value: str
    match: str
    directory: bool


@dataclass(frozen=True)
class MatchPattern:
    """One full-path regular-expression Selection matcher."""

    raw: str

@dataclass(frozen=True)
class SharedReference:
    """One reference to a named set in the field-specific Shared namespace."""

    name: str

@dataclass(frozen=True)
class SharedPatterns:
    """Named reusable pattern sets split by Selection role."""

    must: Mapping[str, tuple[str | MatchPattern, ...]]
    may: Mapping[str, tuple[str | MatchPattern, ...]]
    ignore: Mapping[str, tuple[ExclusionPattern | MatchPattern, ...]]

@dataclass(frozen=True)
class SelectionDefinition:
    """One parsed Selection whose Shared references are not yet materialized."""

    description: str | None
    must: tuple[str | MatchPattern | SharedReference, ...]
    may: tuple[str | MatchPattern | SharedReference, ...]
    ignore: tuple[ExclusionPattern | PathExclusion | MatchPattern | SharedReference, ...]
    allow_empty: bool

@dataclass(frozen=True)
class Selection:
    """One effective Selection with every Shared reference materialized."""

    description: str | None
    must: tuple[str | MatchPattern, ...]
    may: tuple[str | MatchPattern, ...]
    ignore: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
    allow_empty: bool

@dataclass(frozen=True)
class Pluck:
    """The Selection definition applied to runtime directory Targets."""

    default: SelectionDefinition | None
    cases: Mapping[str, SelectionDefinition]

@dataclass(frozen=True)
class Namespace:
    """One archive-only directory namespace available to resolved sources."""

    name: str

@dataclass(frozen=True)
class Scope:
    """One unnamed or named place in which runtime Targets are searched."""

    name: str | None
    path: str | None
    description: str | None
    target_kind: str
    ignore: tuple[TargetIgnorePattern, ...]
    namespace: str | None

@dataclass(frozen=True)
class Always:
    """One Configuration-bound source that participates in every run."""

    name: str
    path: str
    selection: SelectionDefinition
    cases: Mapping[str, SelectionDefinition]
    namespace: str | None

@dataclass(frozen=True)
class Output:
    """One fixed or timestamp-named archive output policy."""

    path: str
    timestamp: bool = False
    overwrite: bool = False
    prefix: str | None = None
    suffix: str | None = None

    @property
    def generated(self) -> bool:
        return self.timestamp

@dataclass(frozen=True)
class Config:
    """One extraction intent described by a dirpluck Configuration file."""

    manifest: Path
    about_description: str | None
    base: str | None
    shared: SharedPatterns
    pluck: Pluck | None
    scopes: Mapping[str | None, Scope]
    always: Mapping[str, Always]
    namespaces: Mapping[str, Namespace]
    output: Output | None

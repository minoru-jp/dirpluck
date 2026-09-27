"""Configuration data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

@dataclass(frozen=True)
class ExclusionPattern:
    """One simple case-sensitive name filter for selected source contents."""

    raw: str
    value: str
    match: str
    directory: bool

@dataclass(frozen=True)
class PathExclusion:
    """One concrete Selection-root-relative path excluded from one source tree."""

    raw: str
    path: str
    directory: bool

@dataclass(frozen=True)
class TargetIgnorePattern:
    """One simple case-sensitive direct-child Target name filter."""

    raw: str
    value: str
    match: str

@dataclass(frozen=True)
class SharedReference:
    """One reference to a named set in the field-specific Shared namespace."""

    name: str

@dataclass(frozen=True)
class SharedPatterns:
    """Named reusable pattern sets split by Selection role."""

    must: Mapping[str, tuple[str, ...]]
    may: Mapping[str, tuple[str, ...]]
    ignore: Mapping[str, tuple[ExclusionPattern, ...]]

@dataclass(frozen=True)
class SelectionDefinition:
    """One parsed Selection whose Shared references are not yet materialized."""

    description: str | None
    must: tuple[str | SharedReference, ...]
    may: tuple[str | SharedReference, ...]
    ignore: tuple[ExclusionPattern | PathExclusion | SharedReference, ...]
    allow_empty: bool

@dataclass(frozen=True)
class Selection:
    """One effective Selection with every Shared reference materialized."""

    description: str | None
    must: tuple[str, ...]
    may: tuple[str, ...]
    ignore: tuple[ExclusionPattern | PathExclusion, ...]
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

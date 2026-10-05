"""Configuration data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping

from ._selection_models import (
    ExclusionPattern,
    IncludePattern,
    MatchPattern,
    PathExclusion,
)
from ._target_models import TargetIgnorePattern, TargetKind


@dataclass(frozen=True)
class SharedReference:
    """One reference to a named set in the field-specific Shared namespace."""

    name: str


@dataclass(frozen=True)
class SharedPatterns:
    """Named reusable pattern sets split by Selection role."""

    must: Mapping[str, tuple[IncludePattern | MatchPattern, ...]]
    may: Mapping[str, tuple[IncludePattern | MatchPattern, ...]]
    ignore: Mapping[str, tuple[ExclusionPattern | MatchPattern, ...]]


@dataclass(frozen=True)
class SelectionDefinition:
    """One parsed Selection whose Shared references are not yet expanded and normalized."""

    description: str | None
    must: tuple[IncludePattern | MatchPattern | SharedReference, ...]
    may: tuple[IncludePattern | MatchPattern | SharedReference, ...]
    ignore: tuple[ExclusionPattern | PathExclusion | MatchPattern | SharedReference, ...]
    allow_empty: bool


@dataclass(frozen=True)
class Scope:
    """One unnamed or named place in which runtime Targets are searched."""

    path: str | None
    description: str | None
    target_kind: TargetKind
    ignore: tuple[TargetIgnorePattern, ...]
    namespace: str | None


@dataclass(frozen=True)
class Always:
    """One Configuration-bound source available to Always Case selection."""

    path: str
    selection: SelectionDefinition
    compatibility_namespace: str | None


@dataclass(frozen=True)
class AlwaysCase:
    """One named filter over the effective Always source collection."""

    description: str | None
    include: tuple[str, ...] | None
    exclude: tuple[str, ...] | None


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
    pluck: SelectionDefinition | None
    pluck_cases: Mapping[str, SelectionDefinition]
    scopes: Mapping[str | None, Scope]
    always: Mapping[str, Always]
    always_cases: Mapping[str, AlwaysCase]
    namespaces: frozenset[str]
    output: Output | None

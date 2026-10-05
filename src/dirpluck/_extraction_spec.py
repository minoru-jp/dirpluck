"""Normalized input contracts consumed by filesystem extraction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._selection_models import Selection
from ._target_models import TargetExpr, TargetIgnorePattern, TargetKind


@dataclass(frozen=True)
class TargetRootSpec:
    """One normalized filesystem root used to resolve Target expressions."""

    name: str | None
    label: str
    root: Path
    description: str | None
    target_kind: TargetKind
    ignore: tuple[TargetIgnorePattern, ...]
    archive_prefix: str | None


@dataclass(frozen=True)
class BoundTargetSpec:
    """One Target expression bound to its normalized filesystem root."""

    expression: TargetExpr
    root: TargetRootSpec
    label: str
    ignore_where: str


@dataclass(frozen=True)
class FixedSourceSpec:
    """One fixed directory source after Configuration semantics are consumed."""

    label: str
    archive_root: str
    root: Path
    selection: Selection


@dataclass(frozen=True)
class ExtractionSpec:
    """Filesystem extraction request with all input-language semantics consumed."""

    targets: tuple[BoundTargetSpec, ...]
    directory_selection: Selection | None
    directory_selection_error: str | None
    fixed_sources: tuple[FixedSourceSpec, ...]

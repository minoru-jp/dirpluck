"""Concrete source models produced by filesystem resolution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from pathlib import Path

from ._selection_models import Selection
from ._target_models import TargetEntryKind


@dataclass(frozen=True)
class ResolvedTarget:
    """One Target expression result before it is bound to a Selection."""

    path: Path
    source_root: str
    archive_root: str
    source_kind: TargetEntryKind
    scope_name: str | None
    scope_description: str | None
    layout_name: str | None


@dataclass(frozen=True)
class ResolvedSource:
    """One concrete Target or fixed source ready for file selection."""

    key: str
    role: Literal["target", "fixed"]
    label: str
    source_kind: TargetEntryKind
    directory: Path
    archive_root: str
    selection: Selection | None
    scope_name: str | None = None
    scope_description: str | None = None
    description: str | None = None
    layout_name: str | None = None

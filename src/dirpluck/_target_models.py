"""Typed models shared by Target parsing, normalization, and resolution."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal, TypeAlias

from .errors import SelectionError


TargetEntryKind = Literal["file", "directory"]
TargetKind = Literal["file", "directory", "both"]


@dataclass(frozen=True)
class TargetItem:
    """One direct-child Target name with its required filesystem kind."""

    name: str
    kind: TargetEntryKind

    @property
    def raw(self) -> str:
        """Return the canonical Target spelling used in diagnostics."""

        return self.name + ("/" if self.kind == "directory" else "")


@dataclass(frozen=True)
class TargetEntryExpr:
    """One direct-child Target request after Scope syntax is removed."""

    item: TargetItem

    @property
    def selector(self) -> bool:
        return False


@dataclass(frozen=True)
class TargetScopeExpr:
    """All eligible direct-child Targets from one already-bound root."""

    @property
    def selector(self) -> bool:
        return False


@dataclass(frozen=True)
class TargetListExpr:
    """One explicit ordered Target list after Scope syntax is removed."""

    items: tuple[TargetItem, ...]

    @property
    def selector(self) -> bool:
        return True


@dataclass(frozen=True)
class TargetRegexExpr:
    """One validated regular-expression Target selector."""

    pattern_text: str
    pattern: re.Pattern[str]

    @property
    def selector(self) -> bool:
        return True


TargetExpr: TypeAlias = TargetEntryExpr | TargetScopeExpr | TargetListExpr | TargetRegexExpr


@dataclass(frozen=True)
class ParsedTargetReference:
    """One parsed Target reference before its Scope name is bound."""

    scope: str | None
    expression: TargetExpr


def validate_target_name(name: str, *, label: str, target_kind: TargetKind = "directory") -> None:
    """Validate one normalized direct-child Target or Scope name."""

    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        noun = {
            "directory": "directory",
            "file": "file",
            "both": "filesystem entry",
        }.get(target_kind)
        if noun is None:
            raise AssertionError(f"unknown Scope target kind: {target_kind}")
        raise SelectionError(f"{label} must name one direct child {noun}: {name!r}")


@dataclass(frozen=True)
class TargetIgnorePattern:
    """One normalized direct-child Target exclusion matcher."""

    raw: str
    value: str
    match: Literal["exact", "prefix", "suffix", "contains"]
    directory: bool

    def matches(self, name: str, *, directory: bool) -> bool:
        if self.directory and not directory:
            return False
        if self.match == "exact":
            return name == self.value
        if self.match == "prefix":
            return name.startswith(self.value)
        if self.match == "suffix":
            return name.endswith(self.value)
        return self.value in name

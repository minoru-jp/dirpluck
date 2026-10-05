"""Normalized Selection models shared by compilation and filesystem extraction."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


@dataclass(frozen=True)
class ExclusionPattern:
    """One normalized case-sensitive name exclusion matcher."""

    raw: str
    value: str
    match: Literal["exact", "prefix", "suffix", "contains"]
    directory: bool

    def matches(self, name: str) -> bool:
        if self.match == "exact":
            return name == self.value
        if self.match == "prefix":
            return name.startswith(self.value)
        if self.match == "suffix":
            return name.endswith(self.value)
        return self.value in name


@dataclass(frozen=True)
class PathExclusion:
    """One normalized Selection-root-relative path exclusion."""

    raw: str
    path: str
    directory: bool

    def matches(self, relative: str, *, candidate_directory: bool) -> bool:
        if relative.startswith(self.path + "/"):
            return True
        if relative != self.path:
            return False
        return candidate_directory or not self.directory


@dataclass(frozen=True)
class MatchPattern:
    """One validated full-path regular-expression Selection matcher."""

    raw: str
    regex: re.Pattern[str]

    def matches(self, relative: str) -> bool:
        return self.regex.fullmatch(relative) is not None


@dataclass(frozen=True)
class IncludeSegment:
    """One normalized path-segment matcher for must/may Selection entries."""

    prefix: str
    suffix: str | None = None

    def matches(self, name: str) -> bool:
        if self.suffix is None:
            return name == self.prefix
        return (
            name.startswith(self.prefix)
            and name.endswith(self.suffix)
            and len(name) >= len(self.prefix) + len(self.suffix)
        )


@dataclass(frozen=True)
class IncludePattern:
    """One normalized must/may path pattern with its required entry kind."""

    path: str
    kind: Literal["file", "directory"]
    segments: tuple[IncludeSegment, ...]

    @property
    def raw(self) -> str:
        return self.path + ("/" if self.kind == "directory" else "")


@dataclass(frozen=True)
class Selection:
    """One effective Selection with every Shared reference expanded and normalized."""

    description: str | None
    must: tuple[IncludePattern | MatchPattern, ...]
    may: tuple[IncludePattern | MatchPattern, ...]
    ignore: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
    allow_empty: bool

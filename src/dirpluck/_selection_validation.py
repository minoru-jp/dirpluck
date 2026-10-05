"""Shared validation helpers for parsed and normalized Selection patterns."""

from __future__ import annotations

from typing import cast

from ._selection_models import (
    ExclusionPattern,
    IncludePattern,
    MatchPattern,
    PathExclusion,
)
from .errors import ConfigurationError

IncludeEntry = IncludePattern | MatchPattern
IgnoreEntry = ExclusionPattern | PathExclusion | MatchPattern
Pattern = IncludeEntry | IgnoreEntry


def selection_entry_key(pattern: Pattern) -> tuple[str, str]:
    """Return one stable semantic identity for a Selection entry."""

    if isinstance(pattern, MatchPattern):
        return ("match", pattern.raw)
    if isinstance(pattern, PathExclusion):
        return ("path", pattern.raw)
    return ("pattern", pattern.raw)


def render_selection_entry(pattern: Pattern) -> str:
    """Render one Selection entry for deterministic diagnostics."""

    if isinstance(pattern, MatchPattern):
        return f"{{ match = {pattern.raw!r} }}"
    if isinstance(pattern, PathExclusion):
        return f"{{ path = {pattern.raw[2:]!r} }}"
    return repr(pattern.raw)


def _reject_duplicates(patterns: tuple[Pattern, ...], where: str) -> None:
    seen: set[tuple[str, str]] = set()
    duplicates: dict[tuple[str, str], Pattern] = {}
    for pattern in patterns:
        key = selection_entry_key(pattern)
        if key in seen:
            _ = duplicates.setdefault(key, pattern)
        seen.add(key)
    if duplicates:
        raise ConfigurationError(
            f"{where}: duplicate effective pattern(s): "
            + ", ".join(render_selection_entry(item) for item in duplicates.values())
        )


def reject_duplicate_selection_entries(patterns: tuple[IncludeEntry, ...], where: str) -> None:
    _reject_duplicates(cast(tuple[Pattern, ...], patterns), where)


def reject_duplicate_exclusions(patterns: tuple[IgnoreEntry, ...], where: str) -> None:
    _reject_duplicates(cast(tuple[Pattern, ...], patterns), where)

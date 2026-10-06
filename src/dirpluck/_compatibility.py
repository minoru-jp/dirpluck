"""Pre-1.0 compatibility helpers scheduled for removal in dirpluck 1.0."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
import os
from pathlib import Path
from typing import cast

from .errors import ConfigurationError
from ._warnings import (
    AlwaysMigrationWarning,
    ConfigurationDeprecationWarning,
    report_dirpluck_warning,
)


@dataclass(frozen=True)
class CompatibilityNotice:
    """One pre-1.0 warning produced during input normalization."""

    message: str
    category: type[Warning]


def report_compatibility_notices(notices: Iterable[CompatibilityNotice]) -> None:
    """Emit normalized compatibility notices through dirpluck's warning channel."""

    for notice in notices:
        report_dirpluck_warning(notice.message, notice.category)


def legacy_reference_array(value: object, where: str, *, label: str = "reference") -> str | None:
    """Parse a deprecated one-element Selection reference array when present."""

    if not isinstance(value, list):
        return None
    legacy = cast(list[object], value)
    if len(legacy) != 1 or not isinstance(legacy[0], str) or not legacy[0].strip():
        raise ConfigurationError(
            f"{where}: {label} must be a one-element array containing a non-empty string"
        )
    return legacy[0]


def _is_legacy_reference(value: object) -> bool:
    if not isinstance(value, list):
        return False
    items = cast(list[object], value)
    return len(items) == 1 and isinstance(items[0], str) and bool(items[0].strip())


def _selection_uses_legacy_reference(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    table = cast(dict[str, object], value)
    for field in ("must", "may", "ignore"):
        entries = table.get(field)
        if isinstance(entries, list) and any(
            _is_legacy_reference(entry) for entry in cast(list[object], entries)
        ):
            return True
    cases = table.get("case")
    return isinstance(cases, dict) and any(
        _selection_uses_legacy_reference(case) for case in cast(dict[str, object], cases).values()
    )


def uses_legacy_selection_reference(data: Mapping[str, object]) -> bool:
    """Return whether a Configuration uses deprecated nested-array references."""

    if _selection_uses_legacy_reference(data.get("pluck")):
        return True
    always = data.get("always")
    if isinstance(always, dict) and any(
        _selection_uses_legacy_reference(source)
        for source in cast(dict[str, object], always).values()
    ):
        return True
    case = data.get("case")
    if not isinstance(case, dict):
        return False
    pluck = cast(dict[str, object], case).get("pluck")
    return isinstance(pluck, dict) and any(
        _selection_uses_legacy_reference(item) for item in cast(dict[str, object], pluck).values()
    )


def split_legacy_pluck_table(value: object) -> tuple[object, object | None, bool]:
    """Separate deprecated [pluck.case] syntax from the canonical [pluck] table."""

    if not isinstance(value, dict):
        return value, None, False
    table = cast(dict[str, object], value)
    if "case" not in table:
        return table, None, False
    canonical = dict(table)
    cases = canonical.pop("case")
    return canonical, cases, True


def warn_legacy_pluck_cases(manifest: Path) -> None:
    report_dirpluck_warning(
        f"{manifest}: [pluck.case.<name>] is deprecated in 0.16.0 and will be removed "
        + "in 1.0.0; use [case.pluck.<name>] instead",
        ConfigurationDeprecationWarning,
    )


def warn_legacy_selection_references(manifest: Path) -> None:
    report_dirpluck_warning(
        f"{manifest}: deprecated nested-array Selection reference syntax since 0.14.0; "
        + 'it will be removed in 1.0.0; use { shared = "..." }, '
        + 'or { path = "..." } for ignore paths',
        ConfigurationDeprecationWarning,
    )


def split_always_namespace(
    table: dict[str, object],
) -> tuple[dict[str, object], object | None, bool]:
    """Separate deprecated Always.namespace from the canonical Always table."""

    if "namespace" not in table:
        return table, None, False
    canonical = dict(table)
    namespace = canonical.pop("namespace")
    return canonical, namespace, True


def warn_always_namespace(where: str, *, namespace: str, source_name: str) -> None:
    report_dirpluck_warning(
        f"{where}.namespace is deprecated and will be removed in 1.0.0: "
        + f"{namespace!r} currently replaces the Always source name {source_name!r} as its "
        + "effective archive name; rename the Always source to the desired archive "
        + "name and remove .namespace before upgrading to 1.0.0",
        AlwaysMigrationWarning,
    )


def always_layout_notice(
    *,
    manifest: Path,
    source_name: str,
    source_root: Path,
    namespace: str | None,
    effective_name: str,
    layout: str | None,
) -> CompatibilityNotice | None:
    """Return the 0.14-to-0.16 Always layout migration notice, if relevant."""

    # An explicit 0.17+ Layout intentionally replaces the final Archive root.
    # The legacy notice compares 0.14.x placement with the 0.16.x
    # Always-name-based placement, so emitting it after a Layout has changed the
    # destination would describe a path that is no longer the effective output.
    if layout is not None:
        return None
    if source_root.parent == source_root:
        return None
    base = Path(os.path.abspath(manifest.parent))
    try:
        relative = source_root.relative_to(base)
    except ValueError:
        old_root = source_root.name
    else:
        old_root = source_root.name if relative == Path(".") else relative.as_posix()
    if namespace is not None:
        old_root = f"{namespace}/{old_root}"
    if old_root == effective_name:
        return None
    return CompatibilityNotice(
        message=(
            f"{manifest} [always.{source_name}]: Always archive layout changed in 0.16.0: "
            + f"0.14.x would place this source under {old_root!r}, while 0.16.x uses "
            + f"{effective_name!r}; update consumers that depend on the previous archive path "
            + "before 1.0.0"
        ),
        category=AlwaysMigrationWarning,
    )

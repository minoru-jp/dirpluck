"""Value-level parsing and validation for Configuration documents."""

from __future__ import annotations

import glob
from collections.abc import Mapping
from pathlib import PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Literal, cast

from ._compatibility import legacy_reference_array
from ._input_paths import CONFIG_SUFFIX, validate_filesystem_location
from ._config_models import SelectionDefinition, SharedPatterns, SharedReference
from ._regex import compile_regular_expression
from ._selection_models import (
    ExclusionPattern,
    IncludePattern,
    IncludeSegment,
    MatchPattern,
    PathExclusion,
)
from ._selection_validation import (
    reject_duplicate_exclusions,
    reject_duplicate_selection_entries,
)
from ._target_models import TargetIgnorePattern
from .errors import ConfigurationError

IncludeEntry = IncludePattern | MatchPattern | SharedReference
IgnoreEntry = ExclusionPattern | PathExclusion | MatchPattern | SharedReference
DirectInclude = IncludePattern | MatchPattern
DirectIgnore = ExclusionPattern | MatchPattern
ParsedEntry = IncludeEntry | IgnoreEntry
DirectPattern = DirectInclude | DirectIgnore


def _table(value: object, where: str, *, optional: bool = False) -> dict[str, object]:
    if value is None and optional:
        return {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    return cast(dict[str, object], value)


def _array(value: object, where: str, *, optional: bool = False) -> list[object]:
    if value is None and optional:
        return []
    if not isinstance(value, list):
        raise ConfigurationError(f"{where}: expected an array")
    return cast(list[object], value)


def _require_only_keys(table: Mapping[str, object], allowed: set[str], where: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise ConfigurationError(f"{where}: unknown key(s): {', '.join(unknown)}")


def _require_name(name: object, where: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ConfigurationError(f"{where}: name must be a non-empty string")
    return name


def _validated_description(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{where}: expected a non-empty string")
    return value.strip()


def _validate_output_fragment(value: object, where: str) -> str | None:  # pyright: ignore[reportUnusedFunction]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigurationError(f"{where}: expected a string")
    if not value.strip():
        raise ConfigurationError(f"{where}: output filename fragment must not be empty")
    if (
        value in {".", ".."}
        or any(char in value for char in '/\\<>:"|?*')
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ConfigurationError(
            f"{where}: output filename fragment must be one portable filename fragment"
        )
    return value


def _validate_base_path(value: object, where: str) -> str:  # pyright: ignore[reportUnusedFunction]
    if not isinstance(value, str):
        raise ConfigurationError(f"{where}: expected a string")
    if value.endswith("/"):
        raise ConfigurationError(f"{where}: base must name one Configuration file")
    path = validate_filesystem_location(value, where, label="base Configuration path")
    if PurePosixPath(path).suffix != CONFIG_SUFFIX:
        raise ConfigurationError(
            f"{where}: base Configuration path must end with {CONFIG_SUFFIX!r}"
        )
    return path


def _normalize_include_pattern(value: str, where: str) -> IncludePattern:
    if not value:
        raise ConfigurationError(f"{where}: include pattern must not be empty")
    if "\\" in value:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in include patterns: {value!r}"
        )

    directory = value.endswith("/")
    body = value[:-1] if directory else value
    if not body:
        raise ConfigurationError(f"{where}: include pattern must name an entry: {value!r}")
    pure = PurePosixPath(body)
    if pure.is_absolute() or pure == PurePosixPath(".") or ".." in pure.parts:
        raise ConfigurationError(
            f"{where}: include pattern must stay inside its directory: {value!r}"
        )
    for part in pure.parts:
        if any(char in part for char in "?[]!"):
            raise ConfigurationError(
                f"{where}: only '*' is supported as a variable name fragment: {value!r}"
            )
        if part.count("*") > 1:
            raise ConfigurationError(
                f"{where}: each path element may contain at most one '*': {value!r}"
            )

    segments = tuple(
        IncludeSegment(*part.split("*", 1)) if "*" in part else IncludeSegment(part)
        for part in pure.parts
    )
    return IncludePattern(
        path=pure.as_posix(),
        kind="directory" if directory else "file",
        segments=segments,
    )


def _parse_name_ignore_pattern(
    raw: str, where: str, *, scope: bool
) -> tuple[str, Literal["exact", "prefix", "suffix", "contains"], bool]:
    if not raw:
        raise ConfigurationError(f"{where}: ignore pattern must not be empty")
    if "\\" in raw:
        label = "Scope ignore patterns" if scope else "ignore patterns"
        raise ConfigurationError(f"{where}: backslashes are not allowed in {label}: {raw!r}")

    directory = raw.endswith("/")
    body = raw[:-1] if directory else raw
    if not body:
        noun = "one direct child entry" if scope else "an entity"
        raise ConfigurationError(f"{where}: ignore pattern must name {noun}: {raw!r}")
    if "/" in body:
        noun = "direct child Target names" if scope else "entity names"
        raise ConfigurationError(f"{where}: ignore patterns match {noun}, not paths: {raw!r}")
    if any(char in body for char in "?[]!"):
        raise ConfigurationError(
            f"{where}: only a leading and/or trailing '*' is supported: {raw!r}"
        )

    if "*" not in body:
        value, match = body, "exact"
    elif body.count("*") == 1 and body.endswith("*"):
        value, match = body[:-1], "prefix"
    elif body.count("*") == 1 and body.startswith("*"):
        value, match = body[1:], "suffix"
    elif body.count("*") == 2 and body.startswith("*") and body.endswith("*"):
        value, match = body[1:-1], "contains"
    else:
        raise ConfigurationError(
            f"{where}: '*' may appear only at the beginning, the end, or both: {raw!r}"
        )
    if not value:
        raise ConfigurationError(f"{where}: '*' and '*/' are not valid ignore patterns")
    return value, match, directory


def _parse_exclusion_pattern(raw: str, where: str) -> ExclusionPattern:
    value, match, directory = _parse_name_ignore_pattern(raw, where, scope=False)
    return ExclusionPattern(raw=raw, value=value, match=match, directory=directory)


def _parse_target_ignore_pattern(raw: str, where: str) -> TargetIgnorePattern:
    value, match, directory = _parse_name_ignore_pattern(raw, where, scope=True)
    return TargetIgnorePattern(raw=raw, value=value, match=match, directory=directory)


def _parse_path_exclusion(raw: str, where: str) -> PathExclusion:
    if not raw:
        raise ConfigurationError(
            f"{where}: ignore path must name an entry below the Selection root"
        )
    if "\\" in raw:
        raise ConfigurationError(f"{where}: backslashes are not allowed in ignore paths: {raw!r}")
    if glob.has_magic(raw):
        raise ConfigurationError(
            f"{where}: ignore path must name one concrete relative path: {raw!r}"
        )

    directory = raw.endswith("/")
    body = raw[:-1] if directory else raw
    pure, windows = PurePosixPath(body), PureWindowsPath(body)
    if (
        pure.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or pure == PurePosixPath(".")
        or ".." in pure.parts
    ):
        raise ConfigurationError(
            f"{where}: ignore path must stay inside the Selection root: {raw!r}"
        )
    normalized = pure.as_posix()
    if normalized in {"", "."}:
        raise ConfigurationError(
            f"{where}: ignore path must name an entry below the Selection root"
        )
    return PathExclusion(
        raw=f"./{normalized}{'/' if directory else ''}",
        path=normalized,
        directory=directory,
    )


def _parse_match_pattern(table: dict[str, object], where: str) -> MatchPattern:
    if set(table) != {"match"}:
        raise ConfigurationError(
            f"{where}: structured Selection entry must be exactly {{ match = ... }}"
        )
    raw = table["match"]
    if not isinstance(raw, str):
        raise ConfigurationError(f"{where}.match: expected a string")
    return MatchPattern(
        raw=raw,
        regex=compile_regular_expression(
            raw,
            where=f"{where}.match",
            error_type=ConfigurationError,
            label="regular expression",
        ),
    )


def _parse_shared_reference(table: dict[str, object], where: str) -> SharedReference:
    raw = table.get("shared") if set(table) == {"shared"} else None
    if not isinstance(raw, str) or not raw.strip():
        raise ConfigurationError(f"{where}.shared: expected a non-empty string")
    return SharedReference(raw)


def _parse_structured_entry(table: dict[str, object], where: str, *, ignore: bool) -> ParsedEntry:
    keys = set(table)
    if keys == {"match"}:
        return _parse_match_pattern(table, where)
    if keys == {"shared"}:
        return _parse_shared_reference(table, where)
    if ignore and keys == {"path"}:
        raw = table["path"]
        if not isinstance(raw, str):
            raise ConfigurationError(f"{where}.path: expected a string")
        return _parse_path_exclusion(raw, f"{where}.path")
    expected = (
        "{ match = ... }, { shared = ... }, or { path = ... }"
        if ignore
        else "{ match = ... } or { shared = ... }"
    )
    raise ConfigurationError(f"{where}: structured Selection entry must be exactly {expected}")


def _parse_selection_entries(value: object, where: str, *, ignore: bool) -> tuple[ParsedEntry, ...]:
    result: list[ParsedEntry] = []
    for index, item in enumerate(_array(value, where, optional=True)):
        item_where = f"{where}[{index}]"
        if isinstance(item, str):
            result.append(
                _parse_exclusion_pattern(item, item_where)
                if ignore
                else _normalize_include_pattern(item, item_where)
            )
            continue
        if isinstance(item, dict):
            result.append(
                _parse_structured_entry(cast(dict[str, object], item), item_where, ignore=ignore)
            )
            continue

        reference = legacy_reference_array(
            item,
            item_where,
            label="reference" if ignore else "Shared reference",
        )
        if reference is None:
            expected = "Selection entry" if ignore else "must/may entry"
            raise ConfigurationError(f"{item_where}: invalid {expected}")
        if ignore and reference.startswith("./"):
            result.append(_parse_path_exclusion(reference, item_where))
        else:
            result.append(SharedReference(reference))
    return tuple(result)


def _parse_direct_patterns(value: object, where: str, *, ignore: bool) -> tuple[DirectPattern, ...]:
    items = _array(value, where)
    if not items:
        raise ConfigurationError(f"{where}: at least one entry is required")
    result: list[DirectPattern] = []
    for index, item in enumerate(items):
        item_where = f"{where}[{index}]"
        if isinstance(item, str):
            result.append(
                _parse_exclusion_pattern(item, item_where)
                if ignore
                else _normalize_include_pattern(item, item_where)
            )
        elif isinstance(item, dict):
            result.append(_parse_match_pattern(cast(dict[str, object], item), item_where))
        else:
            raise ConfigurationError(
                f"{item_where}: expected a direct string pattern or {{ match = ... }} inline table"
            )
    patterns = tuple(result)
    if ignore:
        reject_duplicate_exclusions(
            cast(tuple[ExclusionPattern | MatchPattern, ...], patterns), where
        )
    else:
        reject_duplicate_selection_entries(
            cast(tuple[IncludePattern | MatchPattern, ...], patterns), where
        )
    return patterns


def _parse_shared_namespace(
    value: object, where: str, *, ignore: bool
) -> Mapping[str, tuple[DirectPattern, ...]]:
    if value is None:
        return MappingProxyType({})
    table = _table(value, where)
    if not table:
        raise ConfigurationError(f"{where}: define at least one named pattern set")
    return MappingProxyType(
        {
            _require_name(name, where): _parse_direct_patterns(
                patterns, f"{where}.{name}", ignore=ignore
            )
            for name, patterns in table.items()
        }
    )


def _parse_shared(value: object, where: str) -> SharedPatterns:  # pyright: ignore[reportUnusedFunction]
    if value is None:
        empty: Mapping[str, tuple[DirectInclude, ...]] = MappingProxyType({})
        return SharedPatterns(must=empty, may=empty, ignore=MappingProxyType({}))
    table = _table(value, where)
    _require_only_keys(table, {"must", "may", "ignore"}, where)
    if not table:
        raise ConfigurationError(
            f"{where}: define [shared.must], [shared.may], and/or [shared.ignore]"
        )

    must = cast(
        Mapping[str, tuple[DirectInclude, ...]],
        _parse_shared_namespace(table.get("must"), f"{where}.must", ignore=False),
    )
    may = cast(
        Mapping[str, tuple[DirectInclude, ...]],
        _parse_shared_namespace(table.get("may"), f"{where}.may", ignore=False),
    )
    ignore = cast(
        Mapping[str, tuple[DirectIgnore, ...]],
        _parse_shared_namespace(table.get("ignore"), f"{where}.ignore", ignore=True),
    )
    if not must and not may and not ignore:
        raise ConfigurationError(
            f"{where}: define [shared.must], [shared.may], and/or [shared.ignore]"
        )
    return SharedPatterns(must=must, may=may, ignore=ignore)


def _parse_selection(value: object, where: str) -> SelectionDefinition:
    table = _table(value, where)
    _require_only_keys(table, {"description", "must", "may", "ignore", "allow_empty"}, where)
    description = (
        _validated_description(table["description"], f"{where}.description")
        if "description" in table
        else None
    )
    must = cast(
        tuple[IncludeEntry, ...],
        _parse_selection_entries(table.get("must"), f"{where}.must", ignore=False),
    )
    may = cast(
        tuple[IncludeEntry, ...],
        _parse_selection_entries(table.get("may"), f"{where}.may", ignore=False),
    )
    ignore = cast(
        tuple[IgnoreEntry, ...],
        _parse_selection_entries(table.get("ignore"), f"{where}.ignore", ignore=True),
    )
    if not must and not may:
        raise ConfigurationError(
            f"{where}: at least one must/may pattern or Shared reference is required"
        )

    allow_empty = table.get("allow_empty", False)
    if not isinstance(allow_empty, bool):
        raise ConfigurationError(f"{where}.allow_empty: expected a boolean")
    if allow_empty and must:
        raise ConfigurationError(
            f"{where}.allow_empty: true cannot be used when must entries are declared"
        )
    return SelectionDefinition(
        description=description,
        must=must,
        may=may,
        ignore=ignore,
        allow_empty=allow_empty,
    )


def _parse_cases(value: object, where: str) -> Mapping[str, SelectionDefinition]:  # pyright: ignore[reportUnusedFunction]
    if value is None:
        return MappingProxyType({})
    table = _table(value, where)
    if not table:
        raise ConfigurationError(f"{where}: define at least one named case")
    cases: dict[str, SelectionDefinition] = {}
    for raw_name, raw_case in table.items():
        name = _require_name(raw_name, where)
        if "." in name:
            raise ConfigurationError(
                f"{where}: case names must be flat and must not contain '.': {name!r}"
            )
        cases[name] = _parse_selection(raw_case, f"{where}.{name}")
    return MappingProxyType(cases)


def _parse_pluck(value: object, where: str) -> SelectionDefinition | None:  # pyright: ignore[reportUnusedFunction]
    if value is None:
        return None
    table = _table(value, where)
    return None if not table else _parse_selection(table, where)


def _validated_target_ignores(value: object, where: str) -> tuple[TargetIgnorePattern, ...]:  # pyright: ignore[reportUnusedFunction]
    if value is None:
        return ()
    items = _array(value, where)
    if any(not isinstance(item, str) for item in items):
        raise ConfigurationError(f"{where}: expected an array of strings")
    patterns = tuple(_parse_target_ignore_pattern(cast(str, item), where) for item in items)
    if len({item.raw for item in patterns}) != len(patterns):
        raise ConfigurationError(f"{where}: duplicate ignore patterns are not allowed")
    return patterns


def _validate_scope_name(name: object, where: str) -> str:  # pyright: ignore[reportUnusedFunction]
    value = _require_name(name, where)
    if value in {".", ".."} or "." in value or "/" in value or "\\" in value:
        raise ConfigurationError(
            f"{where}: Scope names must be one non-dot path segment: {value!r}"
        )
    return value


def _validate_archive_directory_name(name: object, where: str, *, label: str) -> str:
    value = _require_name(name, where)
    if (
        value in {".", ".."}
        or "/" in value
        or "\\" in value
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ConfigurationError(
            f"{where}: {label} must be one Archive directory component without path separators or control characters: {value!r}"
        )
    return value


def _validate_namespace_name(name: object, where: str) -> str:
    return _validate_archive_directory_name(name, where, label="Namespace names")


def _validate_always_name(name: object, where: str) -> str:  # pyright: ignore[reportUnusedFunction]
    return _validate_archive_directory_name(name, where, label="Always source names")


def _parse_namespace_reference(value: object, where: str) -> str | None:  # pyright: ignore[reportUnusedFunction]
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigurationError(f"{where}: expected a string")
    return _validate_namespace_name(value, where)

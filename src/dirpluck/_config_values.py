"""Value-level parsing and validation for Configuration documents."""

from __future__ import annotations

import glob
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Mapping

from ._config_models import (
    ExclusionPattern,
    MatchPattern,
    Pluck,
    PathExclusion,
    Selection,
    SelectionDefinition,
    SharedPatterns,
    SharedReference,
    TargetIgnorePattern,
)
from .errors import ConfigurationError
from ._regex import compile_regular_expression

CONFIG_NAME = "default.dirpluck"
CONFIG_SUFFIX = ".dirpluck"

def _config_reference(reference: str | None) -> str:
    """Normalize one CLI Configuration reference to a concrete document path."""

    if reference is None:
        return CONFIG_NAME
    if not isinstance(reference, str) or not reference.strip():
        raise ConfigurationError("configuration path must be a non-empty string")
    raw = reference.strip()
    if raw.endswith("/") or raw.rsplit("/", 1)[-1] in {".", ".."}:
        raise ConfigurationError("configuration path must name one Configuration file")
    path = _validate_filesystem_location(raw, "--config", label="Configuration path")
    if not path.endswith(CONFIG_SUFFIX):
        path += CONFIG_SUFFIX
    return path

def _lexical_absolute_path(path: str | Path, *, cwd: Path | None = None) -> Path:
    """Return an absolute path without resolving symbolic links or other aliases."""

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (cwd or Path.cwd()) / candidate
    return Path(os.path.abspath(candidate))

def resolve_config_path(reference: str | None = None, *, cwd: Path | None = None) -> Path:
    """Resolve one explicit Configuration path, or cwd/default.dirpluck by default."""

    normalized = _config_reference(reference)
    candidate = _lexical_absolute_path(normalized, cwd=cwd)
    if not candidate.is_file():
        raise ConfigurationError(f"configuration file was not found: {candidate}")
    return candidate

def _require_only_keys(table: Mapping[str, object], allowed: set[str], where: str) -> None:
    unknown = sorted(str(key) for key in set(table) - allowed)
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

def _normalize_include_pattern(value: str, where: str) -> str:
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
    normalized = pure.as_posix()
    return normalized + ("/" if directory else "")

def _parse_exclusion_pattern(raw: str, where: str) -> ExclusionPattern:
    if not raw:
        raise ConfigurationError(f"{where}: ignore pattern must not be empty")
    if "\\" in raw:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in ignore patterns: {raw!r}"
        )
    directory = raw.endswith("/")
    body = raw[:-1] if directory else raw
    if not body:
        raise ConfigurationError(f"{where}: ignore pattern must name an entity: {raw!r}")
    if "/" in body:
        raise ConfigurationError(
            f"{where}: ignore patterns match entity names, not paths: {raw!r}"
        )
    if any(char in body for char in "?[]!"):
        raise ConfigurationError(
            f"{where}: only a leading and/or trailing '*' is supported: {raw!r}"
        )
    star_count = body.count("*")
    if star_count == 0:
        match, value = "exact", body
    elif star_count == 1 and body.endswith("*"):
        match, value = "prefix", body[:-1]
    elif star_count == 1 and body.startswith("*"):
        match, value = "suffix", body[1:]
    elif star_count == 2 and body.startswith("*") and body.endswith("*"):
        match, value = "contains", body[1:-1]
    else:
        raise ConfigurationError(
            f"{where}: '*' may appear only at the beginning, the end, or both: {raw!r}"
        )
    if not value:
        raise ConfigurationError(f"{where}: '*' and '*/' are not valid ignore patterns")
    return ExclusionPattern(raw=raw, value=value, match=match, directory=directory)


def _parse_path_exclusion(raw: str, where: str) -> PathExclusion:
    """Parse one concrete Selection-root-relative ignore path reference."""

    if not raw.startswith("./"):
        raise ConfigurationError(f"{where}: ignore path reference must start with './'")
    if "\\" in raw:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in ignore path references: {raw!r}"
        )
    if glob.has_magic(raw):
        raise ConfigurationError(
            f"{where}: ignore path reference must name one concrete relative path: {raw!r}"
        )

    directory = raw.endswith("/")
    body = raw[2:-1] if directory else raw[2:]
    if not body:
        raise ConfigurationError(
            f"{where}: ignore path reference must name an entry below the Selection root"
        )
    pure = PurePosixPath(body)
    if pure.is_absolute() or pure == PurePosixPath(".") or ".." in pure.parts:
        raise ConfigurationError(
            f"{where}: ignore path reference must stay inside the Selection root: {raw!r}"
        )
    normalized = pure.as_posix()
    if normalized in {"", "."}:
        raise ConfigurationError(
            f"{where}: ignore path reference must name an entry below the Selection root"
        )
    canonical = f"./{normalized}{'/' if directory else ''}"
    return PathExclusion(raw=canonical, path=normalized, directory=directory)

def _parse_target_ignore_pattern(raw: str, where: str) -> TargetIgnorePattern:
    if not raw:
        raise ConfigurationError(f"{where}: ignore pattern must not be empty")
    if "\\" in raw:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in Scope ignore patterns: {raw!r}"
        )
    directory = raw.endswith("/")
    body = raw[:-1] if directory else raw
    if not body:
        raise ConfigurationError(f"{where}: ignore pattern must name one direct child entry: {raw!r}")
    if "/" in body:
        raise ConfigurationError(
            f"{where}: ignore patterns match direct child Target names, not paths: {raw!r}"
        )
    if any(char in body for char in "?[]!"):
        raise ConfigurationError(
            f"{where}: only a leading and/or trailing '*' is supported: {raw!r}"
        )
    star_count = body.count("*")
    if star_count == 0:
        match, value = "exact", body
    elif star_count == 1 and body.endswith("*"):
        match, value = "prefix", body[:-1]
    elif star_count == 1 and body.startswith("*"):
        match, value = "suffix", body[1:]
    elif star_count == 2 and body.startswith("*") and body.endswith("*"):
        match, value = "contains", body[1:-1]
    else:
        raise ConfigurationError(
            f"{where}: '*' may appear only at the beginning, the end, or both: {raw!r}"
        )
    if not value:
        raise ConfigurationError(f"{where}: '*' and '*/' are not valid ignore patterns")
    return TargetIgnorePattern(raw=raw, value=value, match=match, directory=directory)

def _validate_filesystem_location(path: str, where: str, *, label: str) -> str:
    """Validate one concrete host filesystem location written with '/' separators."""

    if not path:
        raise ConfigurationError(f"{where}: {label} must not be empty")
    if "\\" in path:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in filesystem locations; use '/' as the path separator"
        )
    if glob.has_magic(path):
        raise ConfigurationError(f"{where}: {label} must name one concrete path")

    pure = PurePosixPath(path)
    windows = PureWindowsPath(path)
    host = Path(path)
    has_non_host_root = (
        (pure.is_absolute() or bool(windows.drive) or bool(windows.root))
        and not host.is_absolute()
    )
    if has_non_host_root:
        raise ConfigurationError(
            f"{where}: absolute-root form is not supported by the host operating system"
        )
    return pure.as_posix()

def _validate_output_fragment(value: object, where: str) -> str | None:
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

def _validate_base_path(value: object, where: str) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{where}: expected a string")
    if value.endswith("/"):
        raise ConfigurationError(f"{where}: base must name one Configuration file")
    path = _validate_filesystem_location(value, where, label="base Configuration path")
    if PurePosixPath(path).suffix != CONFIG_SUFFIX:
        raise ConfigurationError(
            f"{where}: base Configuration path must end with {CONFIG_SUFFIX!r}"
        )
    return path


def _parse_match_pattern(value: object, where: str) -> MatchPattern:
    if not isinstance(value, dict):
        raise AssertionError("match pattern parser requires an inline table")
    _require_only_keys(value, {"match"}, where)
    if "match" not in value:
        raise ConfigurationError(f"{where}: structured Selection entry requires 'match'")
    raw = value["match"]
    if not isinstance(raw, str):
        raise ConfigurationError(f"{where}.match: expected a string")
    compile_regular_expression(
        raw,
        where=f"{where}.match",
        error_type=ConfigurationError,
        label="regular expression",
    )
    return MatchPattern(raw=raw)

def _parse_direct_include_array(
    value: object,
    where: str,
    *,
    allow_empty: bool,
) -> tuple[str | MatchPattern, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{where}: expected an array")
    if not value and not allow_empty:
        raise ConfigurationError(f"{where}: at least one entry is required")
    patterns: list[str | MatchPattern] = []
    for index, item in enumerate(value):
        item_where = f"{where}[{index}]"
        if isinstance(item, str):
            patterns.append(_normalize_include_pattern(item, item_where))
        elif isinstance(item, dict):
            patterns.append(_parse_match_pattern(item, item_where))
        else:
            raise ConfigurationError(
                f"{item_where}: expected a direct string pattern or {{ match = ... }} inline table"
            )
    _reject_duplicate_selection_entries(tuple(patterns), where)
    return tuple(patterns)

def _parse_direct_ignore_array(
    value: object,
    where: str,
    *,
    allow_empty: bool,
) -> tuple[ExclusionPattern | MatchPattern, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{where}: expected an array")
    if not value and not allow_empty:
        raise ConfigurationError(f"{where}: at least one entry is required")
    patterns: list[ExclusionPattern | MatchPattern] = []
    for index, item in enumerate(value):
        item_where = f"{where}[{index}]"
        if isinstance(item, str):
            patterns.append(_parse_exclusion_pattern(item, item_where))
        elif isinstance(item, dict):
            patterns.append(_parse_match_pattern(item, item_where))
        else:
            raise ConfigurationError(
                f"{item_where}: expected a direct string pattern or {{ match = ... }} inline table"
            )
    _reject_duplicate_exclusions(tuple(patterns), where)
    return tuple(patterns)

def _parse_shared_include_namespace(
    value: object,
    where: str,
) -> Mapping[str, tuple[str | MatchPattern, ...]]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one named pattern set")
    result: dict[str, tuple[str | MatchPattern, ...]] = {}
    for raw_name, raw_patterns in value.items():
        name = _require_name(raw_name, where)
        result[name] = _parse_direct_include_array(
            raw_patterns,
            f"{where}.{name}",
            allow_empty=False,
        )
    return MappingProxyType(result)

def _parse_shared_ignore_namespace(
    value: object,
    where: str,
) -> Mapping[str, tuple[ExclusionPattern | MatchPattern, ...]]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one named pattern set")
    result: dict[str, tuple[ExclusionPattern | MatchPattern, ...]] = {}
    for raw_name, raw_patterns in value.items():
        name = _require_name(raw_name, where)
        result[name] = _parse_direct_ignore_array(
            raw_patterns,
            f"{where}.{name}",
            allow_empty=False,
        )
    return MappingProxyType(result)

def _parse_shared(value: object, where: str) -> SharedPatterns:
    if value is None:
        return SharedPatterns(
            must=MappingProxyType({}),
            may=MappingProxyType({}),
            ignore=MappingProxyType({}),
        )
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(value, {"must", "may", "ignore"}, where)
    if not value:
        raise ConfigurationError(
            f"{where}: define [shared.must], [shared.may], and/or [shared.ignore]"
        )
    must = _parse_shared_include_namespace(value.get("must"), f"{where}.must")
    may = _parse_shared_include_namespace(value.get("may"), f"{where}.may")
    ignore = _parse_shared_ignore_namespace(value.get("ignore"), f"{where}.ignore")
    if not must and not may and not ignore:
        raise ConfigurationError(
            f"{where}: define [shared.must], [shared.may], and/or [shared.ignore]"
        )
    return SharedPatterns(must=must, may=may, ignore=ignore)

def _parse_include_items(
    value: object,
    where: str,
) -> tuple[str | MatchPattern | SharedReference, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ConfigurationError(f"{where}: expected an array")
    result: list[str | MatchPattern | SharedReference] = []
    for index, item in enumerate(value):
        item_where = f"{where}[{index}]"
        if isinstance(item, str):
            result.append(_normalize_include_pattern(item, item_where))
            continue
        if isinstance(item, dict):
            result.append(_parse_match_pattern(item, item_where))
            continue
        if isinstance(item, list):
            if len(item) != 1 or not isinstance(item[0], str) or not item[0].strip():
                raise ConfigurationError(
                    f"{item_where}: Shared reference must be a one-element array "
                    "containing a non-empty string"
                )
            result.append(SharedReference(item[0]))
            continue
        raise ConfigurationError(
            f"{item_where}: expected a direct string pattern, {{ match = ... }} inline table, "
            "or one-element Shared reference array"
        )
    return tuple(result)

def _parse_ignore_items(
    value: object,
    where: str,
) -> tuple[ExclusionPattern | PathExclusion | MatchPattern | SharedReference, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ConfigurationError(f"{where}: expected an array")
    result: list[ExclusionPattern | PathExclusion | MatchPattern | SharedReference] = []
    for index, item in enumerate(value):
        item_where = f"{where}[{index}]"
        if isinstance(item, str):
            result.append(_parse_exclusion_pattern(item, item_where))
            continue
        if isinstance(item, dict):
            result.append(_parse_match_pattern(item, item_where))
            continue
        if isinstance(item, list):
            if len(item) != 1 or not isinstance(item[0], str) or not item[0].strip():
                raise ConfigurationError(
                    f"{item_where}: reference must be a one-element array containing a non-empty string"
                )
            reference = item[0]
            if reference.startswith("./"):
                result.append(_parse_path_exclusion(reference, item_where))
            else:
                result.append(SharedReference(reference))
            continue
        raise ConfigurationError(
            f"{item_where}: expected a direct string pattern, {{ match = ... }} inline table, "
            "or one-element reference array"
        )
    return tuple(result)

def _expand_include_items(
    items: tuple[str | MatchPattern | SharedReference, ...],
    namespace: Mapping[str, tuple[str | MatchPattern, ...]],
    where: str,
) -> tuple[str | MatchPattern, ...]:
    expanded: list[str | MatchPattern] = []
    for item in items:
        if isinstance(item, SharedReference):
            try:
                expanded.extend(namespace[item.name])
            except KeyError as exc:
                raise ConfigurationError(
                    f"{where}: unknown Shared pattern set: {item.name!r}"
                ) from exc
        else:
            expanded.append(item)
    return tuple(expanded)

def _expand_ignore_items(
    items: tuple[ExclusionPattern | PathExclusion | MatchPattern | SharedReference, ...],
    namespace: Mapping[str, tuple[ExclusionPattern | MatchPattern, ...]],
    where: str,
) -> tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]:
    expanded: list[ExclusionPattern | PathExclusion | MatchPattern] = []
    for item in items:
        if isinstance(item, SharedReference):
            try:
                expanded.extend(namespace[item.name])
            except KeyError as exc:
                raise ConfigurationError(
                    f"{where}: unknown Shared pattern set: {item.name!r}"
                ) from exc
        else:
            expanded.append(item)
    return tuple(expanded)

def _selection_entry_key(pattern: str | MatchPattern) -> tuple[str, str]:
    if isinstance(pattern, MatchPattern):
        return ("match", pattern.raw)
    return ("pattern", pattern)


def _selection_entry_repr(pattern: str | MatchPattern) -> str:
    if isinstance(pattern, MatchPattern):
        return f"{{ match = {pattern.raw!r} }}"
    return repr(pattern)


def _reject_duplicate_selection_entries(
    patterns: tuple[str | MatchPattern, ...], where: str
) -> None:
    seen: set[tuple[str, str]] = set()
    duplicates: list[str | MatchPattern] = []
    duplicate_keys: set[tuple[str, str]] = set()
    for pattern in patterns:
        key = _selection_entry_key(pattern)
        if key in seen and key not in duplicate_keys:
            duplicates.append(pattern)
            duplicate_keys.add(key)
        seen.add(key)
    if duplicates:
        raise ConfigurationError(
            f"{where}: duplicate effective pattern(s): "
            + ", ".join(_selection_entry_repr(item) for item in duplicates)
        )

def _exclusion_entry_key(
    pattern: ExclusionPattern | PathExclusion | MatchPattern,
) -> tuple[str, str]:
    if isinstance(pattern, MatchPattern):
        return ("match", pattern.raw)
    if isinstance(pattern, PathExclusion):
        return ("path", pattern.raw)
    return ("pattern", pattern.raw)


def _exclusion_entry_repr(pattern: ExclusionPattern | PathExclusion | MatchPattern) -> str:
    if isinstance(pattern, MatchPattern):
        return f"{{ match = {pattern.raw!r} }}"
    return repr(pattern.raw)


def _reject_duplicate_exclusions(
    patterns: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...], where: str
) -> None:
    seen: set[tuple[str, str]] = set()
    duplicates: list[ExclusionPattern | PathExclusion | MatchPattern] = []
    duplicate_keys: set[tuple[str, str]] = set()
    for pattern in patterns:
        key = _exclusion_entry_key(pattern)
        if key in seen and key not in duplicate_keys:
            duplicates.append(pattern)
            duplicate_keys.add(key)
        seen.add(key)
    if duplicates:
        raise ConfigurationError(
            f"{where}: duplicate effective pattern(s): "
            + ", ".join(_exclusion_entry_repr(item) for item in duplicates)
        )

def _parse_selection(value: object, where: str) -> SelectionDefinition:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(value, {"description", "must", "may", "ignore", "allow_empty"}, where)
    description = None
    if "description" in value:
        description = _validated_description(value["description"], f"{where}.description")
    must = _parse_include_items(value.get("must"), f"{where}.must")
    may = _parse_include_items(value.get("may"), f"{where}.may")
    ignore = _parse_ignore_items(value.get("ignore"), f"{where}.ignore")
    if not must and not may:
        raise ConfigurationError(
            f"{where}: at least one must/may pattern or Shared reference is required"
        )

    raw_allow_empty = value.get("allow_empty", False)
    if not isinstance(raw_allow_empty, bool):
        raise ConfigurationError(f"{where}.allow_empty: expected a boolean")
    if raw_allow_empty and must:
        raise ConfigurationError(
            f"{where}.allow_empty: true cannot be used when must entries are declared"
        )

    return SelectionDefinition(
        description=description,
        must=must,
        may=may,
        ignore=ignore,
        allow_empty=raw_allow_empty,
    )

def _materialize_selection(
    selection: SelectionDefinition,
    shared: SharedPatterns,
    where: str,
) -> Selection:
    must = _expand_include_items(selection.must, shared.must, f"{where}.must")
    may = _expand_include_items(selection.may, shared.may, f"{where}.may")
    ignore = _expand_ignore_items(selection.ignore, shared.ignore, f"{where}.ignore")
    _reject_duplicate_selection_entries(must, f"{where}.must")
    _reject_duplicate_selection_entries(may, f"{where}.may")
    must_by_key = {_selection_entry_key(item): item for item in must}
    may_keys = {_selection_entry_key(item) for item in may}
    overlap_keys = sorted(set(must_by_key) & may_keys)
    if overlap_keys:
        overlap = [must_by_key[key] for key in overlap_keys]
        raise ConfigurationError(
            f"{where}: must and may must not contain the same pattern(s): "
            + ", ".join(_selection_entry_repr(item) for item in overlap)
        )
    _reject_duplicate_exclusions(ignore, f"{where}.ignore")
    if selection.allow_empty and must:
        raise ConfigurationError(
            f"{where}.allow_empty: true cannot be used when effective must patterns exist"
        )
    return Selection(
        description=selection.description,
        must=must,
        may=may,
        ignore=ignore,
        allow_empty=selection.allow_empty,
    )

def _parse_cases(value: object, where: str) -> Mapping[str, SelectionDefinition]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one named case")
    cases: dict[str, SelectionDefinition] = {}
    for raw_name, raw_case in value.items():
        name = _require_name(raw_name, where)
        if "." in name:
            raise ConfigurationError(f"{where}: case names must be flat and must not contain '.': {name!r}")
        cases[name] = _parse_selection(raw_case, f"{where}.{name}")
    return MappingProxyType(cases)

def _parse_pluck(value: object, where: str) -> Pluck | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(value, {"description", "must", "may", "ignore", "allow_empty", "case"}, where)
    selection_keys = {"description", "must", "may", "ignore", "allow_empty"}
    has_default = any(key in value for key in selection_keys)
    default = None
    if has_default:
        default = _parse_selection(
            {key: value[key] for key in selection_keys if key in value},
            where,
        )
    cases = _parse_cases(value.get("case"), f"{where}.case")
    if default is None and not cases:
        raise ConfigurationError(f"{where}: define the default pluck or at least one [pluck.case.<name>]")
    return Pluck(default=default, cases=cases)

def _validated_target_ignores(value: object, where: str) -> tuple[TargetIgnorePattern, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ConfigurationError(f"{where}: expected an array of strings")
    patterns = tuple(_parse_target_ignore_pattern(item, where) for item in value)
    raws = tuple(item.raw for item in patterns)
    if len(set(raws)) != len(raws):
        raise ConfigurationError(f"{where}: duplicate ignore patterns are not allowed")
    return patterns

def _validate_scope_name(name: object, where: str) -> str:
    value = _require_name(name, where)
    if value in {".", ".."} or "." in value or "/" in value or "\\" in value:
        raise ConfigurationError(f"{where}: Scope names must be one non-dot path segment: {value!r}")
    return value

def _validate_namespace_name(name: object, where: str) -> str:
    value = _require_name(name, where)
    if (
        value in {".", ".."}
        or any(char in value for char in '/\\<>:"|?*')
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ConfigurationError(
            f"{where}: Namespace names must be one portable archive directory name: {value!r}"
        )
    return value

def _parse_namespace_reference(value: object, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ConfigurationError(f"{where}: expected a string")
    return _validate_namespace_name(value, where)

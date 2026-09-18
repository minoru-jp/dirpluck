"""Strict parsing for the dirpluck configuration file."""

from __future__ import annotations

from dataclasses import dataclass
import glob
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Mapping
import tomllib

from .errors import ConfigurationError

CONFIG_NAME = "dirpluck.toml"
CONFIG_DIRECTORY = "dirpluck"


def _config_filename(reference: str | None) -> str:
    """Normalize one configuration name to a simple TOML filename."""

    if reference is None:
        return CONFIG_NAME
    if not isinstance(reference, str) or not reference.strip():
        raise ConfigurationError("configuration name must be a non-empty string")
    name = reference.strip()
    candidate = Path(name)
    if candidate.name != name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ConfigurationError(
            "configuration name must be a filename, not a path; "
            f"searched locations are ./ and ./{CONFIG_DIRECTORY}/"
        )
    if candidate.suffix == "":
        name += ".toml"
    elif candidate.suffix != ".toml":
        raise ConfigurationError("configuration name must end with '.toml'")
    return name


def find_config_paths(reference: str | None = None, *, cwd: Path | None = None) -> tuple[Path, ...]:
    """Find exact-name configuration candidates in the two supported search directories."""

    root = (cwd or Path.cwd()).resolve()
    filename = _config_filename(reference)
    candidates = (root / filename, root / CONFIG_DIRECTORY / filename)
    return tuple(path for path in candidates if path.is_file())


def resolve_config_path(reference: str | None = None, *, cwd: Path | None = None) -> Path:
    """Resolve a configuration name, requiring exactly one matching file."""

    root = (cwd or Path.cwd()).resolve()
    filename = _config_filename(reference)
    matches = find_config_paths(reference, cwd=root)
    if not matches:
        searched = ", ".join(str(path.relative_to(root)) for path in (root / filename, root / CONFIG_DIRECTORY / filename))
        raise ConfigurationError(
            f"configuration '{filename}' was not found; searched: {searched}"
        )
    if len(matches) > 1:
        found = ", ".join(str(path.relative_to(root)) for path in matches)
        raise ConfigurationError(
            f"configuration '{filename}' is ambiguous; found: {found}"
        )
    return matches[0]


def _looks_like_root_config(path: Path) -> bool:
    """Return whether a cwd TOML file is structurally recognizable as dirpluck config."""

    if path.name == CONFIG_NAME:
        return True
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return (
        isinstance(data, dict)
        and "output" in data
        and ("target" in data or "companion" in data or "import" in data)
    )


def discover_config_paths(*, cwd: Path | None = None) -> tuple[Path, ...]:
    """List configuration candidates visible from cwd without recursive search."""

    root = (cwd or Path.cwd()).resolve()
    paths: list[Path] = []
    for path in sorted(root.glob("*.toml")):
        if path.is_file() and _looks_like_root_config(path):
            paths.append(path)
    directory = root / CONFIG_DIRECTORY
    if directory.is_dir():
        paths.extend(path for path in sorted(directory.glob("*.toml")) if path.is_file())
    return tuple(paths)


@dataclass(frozen=True)
class ExclusionPattern:
    """One simple case-sensitive name filter."""

    raw: str
    value: str
    match: str
    directory: bool


@dataclass(frozen=True)
class SharedPatterns:
    """Named reusable include and exclude pattern sets."""

    include: Mapping[str, tuple[str, ...]]
    exclude: Mapping[str, tuple[ExclusionPattern, ...]]


@dataclass(frozen=True)
class Selection:
    """Effective selection settings owned directly by one target or companion."""

    description: str
    include: tuple[str, ...]
    include_if_exists: tuple[str, ...]
    exclude: tuple[ExclusionPattern, ...]
    if_empty: str


@dataclass(frozen=True)
class Target:
    """One optional CLI-bound source definition with a default selection and named cases."""

    default: Selection | None
    cases: Mapping[str, Selection]


@dataclass(frozen=True)
class Companion:
    """One configuration-bound source with a base selection and optional cases."""

    name: str
    path: str
    selection: Selection
    cases: Mapping[str, Selection]


@dataclass(frozen=True)
class ConfigurationImport:
    """One named external Configuration plus Root-defined companions in its namespace."""

    name: str
    root: str
    configuration: str
    case: str | None
    companions: Mapping[str, Companion]


@dataclass(frozen=True)
class Output:
    """One fixed or generated archive output policy."""

    path: str | None = None
    if_exists: str | None = None
    directory: str | None = None
    prefix: str | None = None
    timestamp: bool = False
    suffix: str | None = None

    @property
    def generated(self) -> bool:
        return self.directory is not None


@dataclass(frozen=True)
class Config:
    """One extraction intent described by a dirpluck configuration file."""

    manifest: Path
    shared: SharedPatterns
    target: Target | None
    companions: Mapping[str, Companion]
    imports: Mapping[str, ConfigurationImport]
    output: Output


def _read_toml(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"configuration file was not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"{path}: top level must be a table")
    return data


def _require_only_keys(table: Mapping[object, object], allowed: set[str], where: str) -> None:
    unknown = sorted(str(key) for key in set(table) - allowed)
    if unknown:
        raise ConfigurationError(f"{where}: unknown key(s): {', '.join(unknown)}")


def _require_name(name: object, where: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ConfigurationError(f"{where}: name must be a non-empty string")
    return name


def _required_description(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{where}: expected a non-empty string")
    return value.strip()


def _string_list(value: object, where: str, *, allow_empty: bool = False) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ConfigurationError(f"{where}: expected an array of strings")
    result = tuple(value)
    if not result and not allow_empty:
        raise ConfigurationError(f"{where}: at least one entry is required when specified")
    if len(set(result)) != len(result):
        raise ConfigurationError(f"{where}: duplicate entries are not allowed")
    return result


def _normalize_include_pattern(value: str, where: str) -> str:
    if not value:
        raise ConfigurationError(f"{where}: include pattern must not be empty")
    normalized = value.replace("\\", "/")
    pure = PurePosixPath(normalized)
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
    return pure.as_posix()


def _validated_includes(value: object, where: str) -> tuple[str, ...]:
    raw = _string_list(value, where)
    normalized = tuple(_normalize_include_pattern(item, where) for item in raw)
    if len(set(normalized)) != len(normalized):
        raise ConfigurationError(f"{where}: duplicate include patterns are not allowed")
    return normalized


def _parse_exclusion_pattern(raw: str, where: str) -> ExclusionPattern:
    if not raw:
        raise ConfigurationError(f"{where}: exclusion pattern must not be empty")
    if "\\" in raw:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in exclusion patterns: {raw!r}"
        )

    directory = raw.endswith("/")
    body = raw[:-1] if directory else raw
    if not body:
        raise ConfigurationError(f"{where}: exclusion pattern must name an entity: {raw!r}")
    if "/" in body:
        raise ConfigurationError(
            f"{where}: exclusion patterns match entity names, not paths: {raw!r}"
        )
    if any(char in body for char in "?[]!"):
        raise ConfigurationError(
            f"{where}: only a leading and/or trailing '*' is supported: {raw!r}"
        )

    star_count = body.count("*")
    if star_count == 0:
        match = "exact"
        value = body
    elif star_count == 1 and body.endswith("*"):
        match = "prefix"
        value = body[:-1]
    elif star_count == 1 and body.startswith("*"):
        match = "suffix"
        value = body[1:]
    elif star_count == 2 and body.startswith("*") and body.endswith("*"):
        match = "contains"
        value = body[1:-1]
    else:
        raise ConfigurationError(
            f"{where}: '*' may appear only at the beginning, the end, or both: {raw!r}"
        )

    if not value:
        raise ConfigurationError(f"{where}: '*' and '*/' are not valid exclusion patterns")

    return ExclusionPattern(raw=raw, value=value, match=match, directory=directory)


def _validated_exclusions(
    value: object,
    where: str,
    *,
    allow_empty: bool = True,
) -> tuple[ExclusionPattern, ...]:
    raw_patterns = (
        _string_list(value, where, allow_empty=allow_empty) if value is not None else ()
    )
    return tuple(_parse_exclusion_pattern(raw, where) for raw in raw_patterns)


def _parse_shared_pattern_table(
    value: object,
    where: str,
    *,
    kind: str,
) -> Mapping[str, tuple[str, ...] | tuple[ExclusionPattern, ...]]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one named pattern set")

    patterns: dict[str, tuple[str, ...] | tuple[ExclusionPattern, ...]] = {}
    for raw_name, raw_patterns in value.items():
        name = _require_name(raw_name, where)
        pattern_where = f"{where}.{name}"
        if kind == "include":
            patterns[name] = _validated_includes(raw_patterns, pattern_where)
        elif kind == "exclude":
            patterns[name] = _validated_exclusions(
                raw_patterns, pattern_where, allow_empty=False
            )
        else:
            raise AssertionError(f"unknown shared pattern kind: {kind}")
    return MappingProxyType(patterns)


def _parse_shared(value: object, where: str) -> SharedPatterns:
    if value is None:
        return SharedPatterns(
            include=MappingProxyType({}),
            exclude=MappingProxyType({}),
        )
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(value, {"include_patterns", "exclude_patterns"}, where)
    if not value:
        raise ConfigurationError(
            f"{where}: define [shared.include_patterns] and/or [shared.exclude_patterns]"
        )

    include = _parse_shared_pattern_table(
        value.get("include_patterns"),
        f"{where}.include_patterns",
        kind="include",
    )
    exclude = _parse_shared_pattern_table(
        value.get("exclude_patterns"),
        f"{where}.exclude_patterns",
        kind="exclude",
    )
    if not include and not exclude:
        raise ConfigurationError(
            f"{where}: define [shared.include_patterns] and/or [shared.exclude_patterns]"
        )
    return SharedPatterns(include=include, exclude=exclude)


def _pattern_refs(value: object, where: str) -> tuple[str, ...]:
    refs = _string_list(value, where)
    return tuple(_require_name(ref, where) for ref in refs)


def _resolve_include_refs(
    refs: tuple[str, ...],
    shared: SharedPatterns,
    where: str,
) -> tuple[str, ...]:
    resolved: list[str] = []
    for name in refs:
        try:
            resolved.extend(shared.include[name])
        except KeyError as exc:
            raise ConfigurationError(
                f"{where}: unknown shared include pattern set: {name!r}"
            ) from exc
    return tuple(resolved)


def _resolve_exclude_refs(
    refs: tuple[str, ...],
    shared: SharedPatterns,
    where: str,
) -> tuple[ExclusionPattern, ...]:
    resolved: list[ExclusionPattern] = []
    for name in refs:
        try:
            resolved.extend(shared.exclude[name])
        except KeyError as exc:
            raise ConfigurationError(
                f"{where}: unknown shared exclude pattern set: {name!r}"
            ) from exc
    return tuple(resolved)


def _reject_duplicate_effective_includes(patterns: tuple[str, ...], where: str) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for pattern in patterns:
        if pattern in seen and pattern not in duplicates:
            duplicates.append(pattern)
        seen.add(pattern)
    if duplicates:
        raise ConfigurationError(
            f"{where}: duplicate effective include pattern(s): "
            + ", ".join(repr(item) for item in duplicates)
        )


def _reject_duplicate_effective_exclusions(
    patterns: tuple[ExclusionPattern, ...],
    where: str,
) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for pattern in patterns:
        if pattern.raw in seen and pattern.raw not in duplicates:
            duplicates.append(pattern.raw)
        seen.add(pattern.raw)
    if duplicates:
        raise ConfigurationError(
            f"{where}: duplicate effective exclusion pattern(s): "
            + ", ".join(repr(item) for item in duplicates)
        )


def _parse_selection(
    value: object,
    where: str,
    shared: SharedPatterns,
) -> Selection:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(
        value,
        {
            "description",
            "include",
            "include_if_exists",
            "exclude",
            "include_pattern_refs",
            "include_if_exists_pattern_refs",
            "exclude_pattern_refs",
            "if_empty",
        },
        where,
    )
    description = _required_description(value.get("description"), f"{where}.description")

    include_refs = _pattern_refs(
        value.get("include_pattern_refs"), f"{where}.include_pattern_refs"
    )
    optional_refs = _pattern_refs(
        value.get("include_if_exists_pattern_refs"),
        f"{where}.include_if_exists_pattern_refs",
    )
    exclude_refs = _pattern_refs(
        value.get("exclude_pattern_refs"), f"{where}.exclude_pattern_refs"
    )

    include = (
        _resolve_include_refs(include_refs, shared, f"{where}.include_pattern_refs")
        + _validated_includes(value.get("include"), f"{where}.include")
    )
    include_if_exists = (
        _resolve_include_refs(
            optional_refs, shared, f"{where}.include_if_exists_pattern_refs"
        )
        + _validated_includes(
            value.get("include_if_exists"), f"{where}.include_if_exists"
        )
    )
    if not include and not include_if_exists:
        raise ConfigurationError(
            f"{where}: at least one include/include_if_exists pattern or shared include reference is required"
        )
    _reject_duplicate_effective_includes(include, f"{where}.include")
    _reject_duplicate_effective_includes(
        include_if_exists, f"{where}.include_if_exists"
    )
    overlap = sorted(set(include) & set(include_if_exists))
    if overlap:
        raise ConfigurationError(
            f"{where}: include and include_if_exists must not contain the same pattern(s): "
            + ", ".join(repr(item) for item in overlap)
        )

    exclude = (
        _resolve_exclude_refs(exclude_refs, shared, f"{where}.exclude_pattern_refs")
        + _validated_exclusions(value.get("exclude"), f"{where}.exclude")
    )
    _reject_duplicate_effective_exclusions(exclude, f"{where}.exclude")

    if_empty = value.get("if_empty", "error")
    if not isinstance(if_empty, str) or if_empty not in {"error", "allow"}:
        raise ConfigurationError(f"{where}.if_empty: expected 'error' or 'allow'")
    if if_empty == "allow" and include:
        raise ConfigurationError(
            f"{where}.if_empty: 'allow' cannot be used when required include patterns are declared"
        )
    return Selection(
        description=description,
        include=include,
        include_if_exists=include_if_exists,
        exclude=exclude,
        if_empty=if_empty,
    )


def _validate_fixed_path(
    path: str,
    where: str,
    *,
    allow_root: bool = False,
) -> str:
    if not path:
        raise ConfigurationError(f"{where}: path must not be empty")
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    windows = PureWindowsPath(normalized)
    if (
        pure.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or ".." in pure.parts
        or (pure == PurePosixPath(".") and not allow_root)
    ):
        boundary = "at or below" if allow_root else "below"
        raise ConfigurationError(
            f"{where}: fixed path must name a directory {boundary} the Configuration execution root"
        )
    if glob.has_magic(normalized):
        raise ConfigurationError(f"{where}: fixed path must name one concrete directory")
    return pure.as_posix()


def _validate_output_path(path: str, where: str) -> str:
    if not path:
        raise ConfigurationError(f"{where}: output path must not be empty")
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or pure == PurePosixPath(".") or ".." in pure.parts:
        raise ConfigurationError(
            f"{where}: output path must stay below the current working directory"
        )
    if glob.has_magic(normalized):
        raise ConfigurationError(f"{where}: output path must be one concrete path")
    return pure.as_posix()


def _validate_output_directory(path: str, where: str) -> str:
    if not path:
        raise ConfigurationError(f"{where}: output directory must not be empty")
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or ".." in pure.parts:
        raise ConfigurationError(
            f"{where}: output directory must stay inside the current working directory"
        )
    if glob.has_magic(normalized):
        raise ConfigurationError(f"{where}: output directory must be one concrete path")
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


def _validate_import_root(path: str, where: str) -> str:
    if not path:
        raise ConfigurationError(f"{where}: root must not be empty")
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    windows = PureWindowsPath(normalized)
    if pure.is_absolute() or windows.is_absolute() or windows.drive:
        raise ConfigurationError(
            f"{where}: import root must be a portable relative path"
        )
    if glob.has_magic(normalized):
        raise ConfigurationError(f"{where}: import root must name one concrete directory")
    return pure.as_posix()


def _validate_import_configuration(path: str, where: str) -> str:
    if not path:
        raise ConfigurationError(f"{where}: configuration path must not be empty")
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    windows = PureWindowsPath(normalized)
    raw_parts = tuple(part for part in normalized.split("/") if part != "")
    if (
        pure.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or any(part in {".", ".."} for part in raw_parts)
    ):
        raise ConfigurationError(
            f"{where}: configuration must be a relative TOML path without '.' or '..' traversal"
        )
    if glob.has_magic(normalized):
        raise ConfigurationError(f"{where}: configuration must name one concrete TOML file")
    if pure.suffix != ".toml":
        raise ConfigurationError(f"{where}: configuration must end with '.toml'")
    return pure.as_posix()


def _parse_imports(
    value: object,
    where: str,
    shared: SharedPatterns,
) -> Mapping[str, ConfigurationImport]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one named import")

    imports: dict[str, ConfigurationImport] = {}
    for raw_name, raw_import in value.items():
        name = _require_name(raw_name, where)
        import_where = f"{where}.{name}"
        if not isinstance(raw_import, dict):
            raise ConfigurationError(f"{import_where}: expected a table")
        _require_only_keys(
            raw_import, {"root", "configuration", "case", "companion"}, import_where
        )

        raw_root = raw_import.get("root")
        if not isinstance(raw_root, str):
            raise ConfigurationError(f"{import_where}.root: expected a string")
        root = _validate_import_root(raw_root, f"{import_where}.root")

        raw_configuration = raw_import.get("configuration")
        if not isinstance(raw_configuration, str):
            raise ConfigurationError(f"{import_where}.configuration: expected a string")
        configuration = _validate_import_configuration(
            raw_configuration, f"{import_where}.configuration"
        )

        raw_case = raw_import.get("case")
        if raw_case is None:
            case = None
        else:
            case = _require_name(raw_case, f"{import_where}.case")

        companions = _parse_companions(
            raw_import.get("companion"),
            f"{import_where}.companion",
            shared,
            allow_root_path=True,
        )

        imports[name] = ConfigurationImport(
            name=name,
            root=root,
            configuration=configuration,
            case=case,
            companions=companions,
        )
    return MappingProxyType(imports)


def _parse_output(value: object, where: str) -> Output:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: required table is missing")
    _require_only_keys(
        value,
        {"path", "if_exists", "directory", "prefix", "timestamp", "suffix"},
        where,
    )

    uses_fixed = "path" in value or "if_exists" in value
    uses_generated = any(
        key in value for key in {"directory", "prefix", "timestamp", "suffix"}
    )
    if uses_fixed and uses_generated:
        raise ConfigurationError(
            f"{where}: fixed output fields and generated output fields must not be combined"
        )
    if uses_fixed:
        raw_path = value.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{where}.path: expected a string")
        path = _validate_output_path(raw_path, f"{where}.path")

        if_exists = value.get("if_exists")
        if not isinstance(if_exists, str):
            raise ConfigurationError(f"{where}.if_exists: expected a string")
        if if_exists not in {"error", "overwrite"}:
            raise ConfigurationError(f"{where}.if_exists: expected 'error' or 'overwrite'")
        return Output(path=path, if_exists=if_exists)

    if uses_generated:
        raw_directory = value.get("directory")
        if not isinstance(raw_directory, str):
            raise ConfigurationError(f"{where}.directory: expected a string")
        directory = _validate_output_directory(raw_directory, f"{where}.directory")
        if value.get("timestamp") is not True:
            raise ConfigurationError(
                f"{where}.timestamp: generated output requires timestamp = true"
            )
        prefix = _validate_output_fragment(value.get("prefix"), f"{where}.prefix")
        suffix = _validate_output_fragment(value.get("suffix"), f"{where}.suffix")
        return Output(
            directory=directory,
            prefix=prefix,
            timestamp=True,
            suffix=suffix,
        )

    raise ConfigurationError(
        f"{where}: define either fixed output with path + if_exists or generated output with directory + timestamp = true"
    )


def _parse_cases(
    value: object,
    where: str,
    shared: SharedPatterns,
) -> Mapping[str, Selection]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one named case")

    cases: dict[str, Selection] = {}
    for raw_name, raw_case in value.items():
        name = _require_name(raw_name, where)
        if "." in name:
            raise ConfigurationError(
                f"{where}: case names must be flat and must not contain '.': {name!r}"
            )
        cases[name] = _parse_selection(raw_case, f"{where}.{name}", shared)
    return MappingProxyType(cases)


def _parse_target(
    value: object,
    where: str,
    shared: SharedPatterns,
) -> Target | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(
        value,
        {
            "description",
            "include",
            "include_if_exists",
            "exclude",
            "include_pattern_refs",
            "include_if_exists_pattern_refs",
            "exclude_pattern_refs",
            "if_empty",
            "case",
        },
        where,
    )

    default_keys = {
        "description",
        "include",
        "include_if_exists",
        "exclude",
        "include_pattern_refs",
        "include_if_exists_pattern_refs",
        "exclude_pattern_refs",
        "if_empty",
    }
    has_default = any(key in value for key in default_keys)
    default: Selection | None = None
    if has_default:
        default = _parse_selection(
            {key: value[key] for key in default_keys if key in value},
            where,
            shared,
        )

    cases = _parse_cases(value.get("case"), f"{where}.case", shared)

    if default is None and not cases:
        raise ConfigurationError(
            f"{where}: define the default target directly or at least one [target.case.<name>]"
        )
    return Target(default=default, cases=cases)


def _parse_companions(
    value: object,
    where: str,
    shared: SharedPatterns,
    *,
    allow_root_path: bool = False,
) -> Mapping[str, Companion]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")

    companions: dict[str, Companion] = {}
    for raw_name, raw_companion in value.items():
        name = _require_name(raw_name, where)
        companion_where = f"{where}.{name}"
        if not isinstance(raw_companion, dict):
            raise ConfigurationError(f"{companion_where}: expected a table")
        _require_only_keys(
            raw_companion,
            {
                "path",
                "description",
                "include",
                "include_if_exists",
                "exclude",
                "include_pattern_refs",
                "include_if_exists_pattern_refs",
                "exclude_pattern_refs",
                "if_empty",
                "case",
            },
            companion_where,
        )
        raw_path = raw_companion.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{companion_where}.path: expected a string")
        path = _validate_fixed_path(
            raw_path, f"{companion_where}.path", allow_root=allow_root_path
        )
        selection = _parse_selection(
            {
                key: item
                for key, item in raw_companion.items()
                if key not in {"path", "case"}
            },
            companion_where,
            shared,
        )
        cases = _parse_cases(
            raw_companion.get("case"), f"{companion_where}.case", shared
        )
        companions[name] = Companion(
            name=name,
            path=path,
            selection=selection,
            cases=cases,
        )
    return MappingProxyType(companions)


def _validate_case_namespace(
    target: Target | None,
    companions: Mapping[str, Companion],
    where: str,
) -> None:
    if target is None:
        return

    target_cases = set(target.cases)
    for name, companion in companions.items():
        unreachable = sorted(set(companion.cases) - target_cases)
        if unreachable:
            listed = ", ".join(repr(case) for case in unreachable)
            raise ConfigurationError(
                f"{where} [companion.{name}.case]: case(s) not defined by target: {listed}"
            )


def load_config(path: str | Path = CONFIG_NAME) -> Config:
    """Load one dirpluck configuration file without resolving filesystem paths."""

    manifest = Path(path).expanduser().resolve()
    data = _read_toml(manifest)
    _require_only_keys(data, {"shared", "import", "target", "companion", "output"}, str(manifest))

    shared = _parse_shared(data.get("shared"), f"{manifest} [shared]")
    target = _parse_target(data.get("target"), f"{manifest} [target]", shared)
    companions = _parse_companions(
        data.get("companion"), f"{manifest} [companion]", shared
    )
    imports = _parse_imports(data.get("import"), f"{manifest} [import]", shared)
    if target is None and not companions and not imports:
        raise ConfigurationError(
            f"{manifest}: define [target], at least one [companion.<name>], "
            "and/or at least one [import.<name>]"
        )
    _validate_case_namespace(target, companions, str(manifest))
    output = _parse_output(data.get("output"), f"{manifest} [output]")

    return Config(
        manifest=manifest,
        shared=shared,
        target=target,
        companions=companions,
        imports=imports,
        output=output,
    )

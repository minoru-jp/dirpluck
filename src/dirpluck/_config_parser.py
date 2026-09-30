"""TOML schema parsing for dirpluck Configuration documents."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
import inspect
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping
import tomllib
import warnings

from ._config_models import Always, Config, Namespace, Output, Scope
from ._config_values import (
    CONFIG_NAME,
    CONFIG_SUFFIX,
    _lexical_absolute_path,
    _parse_cases,
    _parse_namespace_reference,
    _parse_pluck,
    _parse_selection,
    _parse_shared,
    _require_name,
    _require_only_keys,
    _validate_base_path,
    _validate_filesystem_location,
    _validate_output_fragment,
    _validate_namespace_name,
    _validate_scope_name,
    _validated_description,
    _validated_target_ignores,
)
from .errors import ConfigurationError
from ._warnings import ConfigurationDeprecationWarning


_CONFIGURATION_DEPRECATIONS: ContextVar[list[str] | None] = ContextVar(
    "dirpluck_configuration_deprecations",
    default=None,
)


@contextmanager
def collect_configuration_deprecations() -> Iterator[list[str]]:
    """Collect deprecated Configuration syntax diagnostics for one caller."""

    messages: list[str] = []
    token = _CONFIGURATION_DEPRECATIONS.set(messages)
    try:
        yield messages
    finally:
        _CONFIGURATION_DEPRECATIONS.reset(token)


def _report_configuration_deprecation(message: str) -> None:
    messages = _CONFIGURATION_DEPRECATIONS.get()
    if messages is not None:
        if message not in messages:
            messages.append(message)
        return

    # Attribute API warnings to the first caller outside dirpluck rather than to
    # an internal parser/effective-resolution frame.  The root Configuration
    # and base-chain paths have different depths, so a fixed stacklevel is not
    # a stable API contract.
    stacklevel = 1
    frame = inspect.currentframe()
    try:
        while frame is not None:
            module_name = frame.f_globals.get("__name__", "")
            if module_name != "dirpluck" and not module_name.startswith("dirpluck."):
                break
            stacklevel += 1
            frame = frame.f_back
    finally:
        del frame

    warnings.warn(
        message,
        ConfigurationDeprecationWarning,
        stacklevel=stacklevel,
    )


def _selection_uses_deprecated_reference_syntax(value: object) -> bool:
    """Return whether one Selection table contains a valid legacy nested reference."""

    if not isinstance(value, dict):
        return False
    for field in ("must", "may", "ignore"):
        entries = value.get(field)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if (
                isinstance(entry, list)
                and len(entry) == 1
                and isinstance(entry[0], str)
                and bool(entry[0].strip())
            ):
                return True
    cases = value.get("case")
    if isinstance(cases, dict):
        return any(
            _selection_uses_deprecated_reference_syntax(case)
            for case in cases.values()
        )
    return False


def _uses_deprecated_reference_syntax(data: Mapping[str, object]) -> bool:
    """Return whether this Configuration uses a legacy nested Selection reference."""

    if _selection_uses_deprecated_reference_syntax(data.get("pluck")):
        return True
    always = data.get("always")
    if isinstance(always, dict):
        return any(
            _selection_uses_deprecated_reference_syntax(source)
            for source in always.values()
        )
    return False


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

def _parse_namespaces(value: object, where: str) -> Mapping[str, Namespace]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    if not value:
        raise ConfigurationError(f"{where}: define at least one [namespace.<name>]")
    namespaces: dict[str, Namespace] = {}
    for raw_name, raw_namespace in value.items():
        name = _validate_namespace_name(raw_name, where)
        namespace_where = f"{where}.{name}"
        if not isinstance(raw_namespace, dict):
            raise ConfigurationError(f"{namespace_where}: expected a table")
        _require_only_keys(raw_namespace, set(), namespace_where)
        namespaces[name] = Namespace(name=name)
    return MappingProxyType(namespaces)

def _parse_scope_target_kind(value: object, where: str) -> str:
    if value is None:
        return "directory"
    if not isinstance(value, str):
        raise ConfigurationError(f"{where}: expected 'directory', 'file', or 'both'")
    if value not in {"directory", "file", "both"}:
        raise ConfigurationError(f"{where}: expected 'directory', 'file', or 'both'")
    return value


def _parse_scopes(value: object, where: str) -> Mapping[str | None, Scope]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")

    scopes: dict[str | None, Scope] = {}
    unnamed_description: str | None = None
    unnamed_target_kind = "directory"
    unnamed_ignore: tuple[TargetIgnorePattern, ...] = ()
    unnamed_namespace: str | None = None

    for raw_key, raw_value in value.items():
        if raw_key == "description" and not isinstance(raw_value, dict):
            unnamed_description = _validated_description(raw_value, f"{where}.description")
            continue
        if raw_key == "target_kind" and not isinstance(raw_value, dict):
            unnamed_target_kind = _parse_scope_target_kind(raw_value, f"{where}.target_kind")
            continue
        if raw_key == "ignore" and not isinstance(raw_value, dict):
            unnamed_ignore = _validated_target_ignores(raw_value, f"{where}.ignore")
            continue
        if raw_key == "namespace" and not isinstance(raw_value, dict):
            unnamed_namespace = _parse_namespace_reference(raw_value, f"{where}.namespace")
            continue
        if not isinstance(raw_value, dict):
            if raw_key == "path":
                raise ConfigurationError(f"{where}.path: unnamed [scope] must not define path")
            raise ConfigurationError(f"{where}: unknown key: {raw_key}")

        name = _validate_scope_name(raw_key, where)
        scope_where = f"{where}.{name}"
        _require_only_keys(
            raw_value,
            {"path", "description", "target_kind", "ignore", "namespace"},
            scope_where,
        )
        raw_path = raw_value.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{scope_where}.path: expected a string")
        path = _validate_filesystem_location(raw_path, f"{scope_where}.path", label="Scope path")
        description = None
        if "description" in raw_value:
            description = _validated_description(raw_value["description"], f"{scope_where}.description")
        target_kind = _parse_scope_target_kind(raw_value.get("target_kind"), f"{scope_where}.target_kind")
        ignore = _validated_target_ignores(raw_value.get("ignore"), f"{scope_where}.ignore")
        namespace = _parse_namespace_reference(raw_value.get("namespace"), f"{scope_where}.namespace")
        scopes[name] = Scope(
            name=name,
            path=path,
            description=description,
            target_kind=target_kind,
            ignore=ignore,
            namespace=namespace,
        )

    # The unnamed/default Scope always exists.  [scope] configures its optional
    # metadata, Target kind, ignore policy, and archive namespace; an empty
    # [scope] preserves the historical directory-Target defaults.
    scopes[None] = Scope(
        name=None,
        path=None,
        description=unnamed_description,
        target_kind=unnamed_target_kind,
        ignore=unnamed_ignore,
        namespace=unnamed_namespace,
    )
    return MappingProxyType(scopes)

def _parse_always(value: object, where: str) -> Mapping[str, Always]:
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    always: dict[str, Always] = {}
    for raw_name, raw_source in value.items():
        name = _require_name(raw_name, where)
        source_where = f"{where}.{name}"
        if not isinstance(raw_source, dict):
            raise ConfigurationError(f"{source_where}: expected a table")
        _require_only_keys(raw_source, {"path", "description", "must", "may", "ignore", "allow_empty", "case", "namespace"}, source_where)
        raw_path = raw_source.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{source_where}.path: expected a string")
        path = _validate_filesystem_location(raw_path, f"{source_where}.path", label="Always source path")
        selection = _parse_selection(
            {key: item for key, item in raw_source.items() if key not in {"path", "case", "namespace"}},
            source_where,
        )
        cases = _parse_cases(raw_source.get("case"), f"{source_where}.case")
        namespace = _parse_namespace_reference(raw_source.get("namespace"), f"{source_where}.namespace")
        always[name] = Always(
            name=name,
            path=path,
            selection=selection,
            cases=cases,
            namespace=namespace,
        )
    return MappingProxyType(always)

def _parse_about(value: object, where: str) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(value, {"description", "base"}, where)
    if not value:
        raise ConfigurationError(f"{where}: define description and/or base")
    description = None
    if "description" in value:
        description = _validated_description(value["description"], f"{where}.description")
    base = None
    if "base" in value:
        base = _validate_base_path(value["base"], f"{where}.base")
    return description, base

def _parse_output(value: object, where: str) -> Output | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    _require_only_keys(value, {"path", "overwrite", "timestamp"}, where)

    if "timestamp" in value:
        if "path" in value or "overwrite" in value:
            raise ConfigurationError(f"{where}: fixed output fields and [output.timestamp] are mutually exclusive")
        raw_timestamp = value["timestamp"]
        if not isinstance(raw_timestamp, dict):
            raise ConfigurationError(f"{where}.timestamp: expected a table")
        _require_only_keys(raw_timestamp, {"path", "prefix", "suffix"}, f"{where}.timestamp")
        raw_path = raw_timestamp.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{where}.timestamp.path: expected a string")
        if not raw_path.endswith("/"):
            raise ConfigurationError(f"{where}.timestamp.path: timestamp output directory path must end with '/'")
        path = _validate_filesystem_location(raw_path, f"{where}.timestamp.path", label="output directory")
        prefix = _validate_output_fragment(raw_timestamp.get("prefix"), f"{where}.timestamp.prefix")
        suffix = _validate_output_fragment(raw_timestamp.get("suffix"), f"{where}.timestamp.suffix")
        return Output(path=path, timestamp=True, prefix=prefix, suffix=suffix)

    raw_path = value.get("path")
    if not isinstance(raw_path, str):
        raise ConfigurationError(f"{where}.path: expected a string")
    if raw_path.endswith("/"):
        raise ConfigurationError(f"{where}.path: fixed output path must include a filename and must not end with '/'")
    path = _validate_filesystem_location(raw_path, f"{where}.path", label="output path")
    final_component = raw_path.rsplit("/", 1)[-1]
    if final_component in {".", ".."} or PurePosixPath(path) == PurePosixPath("."):
        raise ConfigurationError(f"{where}.path: output path must name a file")
    overwrite = value.get("overwrite", False)
    if not isinstance(overwrite, bool):
        raise ConfigurationError(f"{where}.overwrite: expected a boolean")
    return Output(path=path, overwrite=overwrite)

def load_config(path: str | Path = CONFIG_NAME) -> Config:
    """Load one dirpluck Configuration document without resolving its base chain."""

    manifest = _lexical_absolute_path(Path(path).expanduser())
    if manifest.suffix != CONFIG_SUFFIX:
        raise ConfigurationError(
            f"configuration file must end with {CONFIG_SUFFIX!r}: {manifest}"
        )
    data = _read_toml(manifest)
    _require_only_keys(data, {"about", "shared", "pluck", "scope", "always", "namespace", "output"}, str(manifest))

    about_description, base = _parse_about(data.get("about"), f"{manifest} [about]")
    shared = _parse_shared(data.get("shared"), f"{manifest} [shared]")
    pluck = _parse_pluck(data.get("pluck"), f"{manifest} [pluck]")
    scopes = _parse_scopes(
        data.get("scope"),
        f"{manifest} [scope]",
    )
    always = _parse_always(data.get("always"), f"{manifest} [always]")
    namespaces = _parse_namespaces(data.get("namespace"), f"{manifest} [namespace]")
    output = _parse_output(data.get("output"), f"{manifest} [output]")

    config = Config(
        manifest=manifest,
        about_description=about_description,
        base=base,
        shared=shared,
        pluck=pluck,
        scopes=scopes,
        always=always,
        namespaces=namespaces,
        output=output,
    )
    if _uses_deprecated_reference_syntax(data):
        _report_configuration_deprecation(
            f"{manifest}: deprecated nested-array Selection reference syntax since 0.14.0; "
            "it will be removed in 1.0.0; use { shared = \"...\" }, "
            "or { path = \"...\" } for ignore paths"
        )
    return config

"""TOML schema parsing for dirpluck Configuration documents."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping
import tomllib

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

def _parse_scopes(value: object, where: str) -> Mapping[str | None, Scope]:
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")

    scopes: dict[str | None, Scope] = {}
    unnamed_ignore: tuple[TargetIgnorePattern, ...] = ()
    unnamed_namespace: str | None = None

    for raw_key, raw_value in value.items():
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
        _require_only_keys(raw_value, {"path", "ignore", "namespace"}, scope_where)
        raw_path = raw_value.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{scope_where}.path: expected a string")
        path = _validate_filesystem_location(raw_path, f"{scope_where}.path", label="Scope path")
        ignore = _validated_target_ignores(raw_value.get("ignore"), f"{scope_where}.ignore")
        namespace = _parse_namespace_reference(raw_value.get("namespace"), f"{scope_where}.namespace")
        scopes[name] = Scope(name=name, path=path, ignore=ignore, namespace=namespace)

    # The unnamed/default Scope always exists.  [scope] configures only its
    # optional ignore policy and archive namespace; an empty [scope] is a no-op.
    scopes[None] = Scope(
        name=None,
        path=None,
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

    return Config(
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

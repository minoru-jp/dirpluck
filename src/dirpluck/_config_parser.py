"""TOML schema parsing for dirpluck Configuration documents."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from types import MappingProxyType
import tomllib
from typing import cast

from ._config_models import (
    Always,
    AlwaysCase,
    Config,
    Layout,
    Output,
    Scope,
    SelectionDefinition,
)
from ._config_values import (
    _array,
    _parse_cases,
    _parse_layout_reference,
    _parse_namespace_reference,
    _parse_pluck,
    _parse_selection,
    _parse_shared,
    _require_only_keys,
    _require_name,
    _validate_always_name,
    _validate_extra_name,
    _validate_base_path,
    _validate_output_fragment,
    _validate_layout_name,
    _validate_namespace_name,
    _validate_scope_name,
    _validated_description,
    _validated_target_ignores,
)
from ._input_paths import (
    CONFIG_NAME,
    CONFIG_SUFFIX,
    lexical_absolute_path,
    validate_filesystem_location,
)
from ._target_models import TargetKind
from .errors import ConfigurationError
from ._compatibility import (
    split_always_namespace,
    split_legacy_pluck_table,
    uses_legacy_selection_reference,
    warn_always_namespace,
    warn_legacy_pluck_cases,
    warn_legacy_selection_references,
)


def _read_toml(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as file:
            raw_data = tomllib.load(file)
    except FileNotFoundError as exc:
        raise ConfigurationError(f"configuration file was not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(raw_data, dict):
        raise ConfigurationError(f"{path}: top level must be a table")
    return cast(dict[str, object], raw_data)


def _table(value: object, where: str, *, none_as_empty: bool = False) -> dict[str, object]:
    if value is None and none_as_empty:
        return {}
    if not isinstance(value, dict):
        raise ConfigurationError(f"{where}: expected a table")
    return cast(dict[str, object], value)


def _description_field(table: Mapping[str, object], key: str, where: str) -> str | None:
    if key not in table:
        return None
    return _validated_description(table[key], f"{where}.{key}")


def _description(table: Mapping[str, object], where: str) -> str | None:
    return _description_field(table, "description", where)


def _require_distinct_casefold(
    name: str,
    seen: dict[str, str],
    where: str,
    *,
    label: str,
) -> None:
    key = name.casefold()
    previous = seen.get(key)
    if previous is not None:
        raise ConfigurationError(
            f"{where}: {label} must be distinct ignoring case: {previous!r} and {name!r}"
        )
    seen[key] = name


def _parse_namespaces(value: object, where: str) -> frozenset[str]:
    table = _table(value, where, none_as_empty=True)
    if not table:
        if value is None:
            return frozenset()
        raise ConfigurationError(f"{where}: define at least one [namespace.<name>]")
    namespaces: set[str] = set()
    namespace_names: dict[str, str] = {}
    for raw_name, raw_namespace in table.items():
        name = _validate_namespace_name(raw_name, where)
        _require_distinct_casefold(name, namespace_names, where, label="Namespace names")
        namespace_where = f"{where}.{name}"
        _require_only_keys(_table(raw_namespace, namespace_where), set(), namespace_where)
        namespaces.add(name)
    return frozenset(namespaces)


def _parse_layouts(value: object, where: str) -> Mapping[str, Layout]:
    if value is None:
        return MappingProxyType({})
    table = _table(value, where)
    if not table:
        raise ConfigurationError(f"{where}: define at least one [layout.<name>]")
    layouts: dict[str, Layout] = {}
    layout_names: dict[str, str] = {}
    for raw_name, raw_layout in table.items():
        name = _validate_layout_name(raw_name, where)
        _require_distinct_casefold(name, layout_names, where, label="Layout names")
        layout_where = f"{where}.{name}"
        layout_table = _table(raw_layout, layout_where)
        _require_only_keys(layout_table, {"description"}, layout_where)
        layouts[name] = Layout(description=_description(layout_table, layout_where))
    return MappingProxyType(layouts)


def _parse_scope_target_kind(value: object, where: str) -> TargetKind:
    if value is None:
        return "directory"
    if not isinstance(value, str) or value not in {"directory", "file", "both"}:
        raise ConfigurationError(f"{where}: expected 'directory', 'file', or 'both'")
    return cast(TargetKind, value)


def _parse_scope(table: dict[str, object], where: str, *, name: str | None) -> Scope:
    allowed = {"description", "target_kind", "ignore", "namespace", "layout"}
    if name is not None:
        allowed.add("path")
    _require_only_keys(table, allowed, where)

    path = None
    if name is not None:
        raw_path = table.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{where}.path: expected a string")
        path = validate_filesystem_location(raw_path, f"{where}.path", label="Scope path")
    return Scope(
        path=path,
        description=_description(table, where),
        target_kind=_parse_scope_target_kind(table.get("target_kind"), f"{where}.target_kind"),
        ignore=_validated_target_ignores(table.get("ignore"), f"{where}.ignore"),
        namespace=_parse_namespace_reference(table.get("namespace"), f"{where}.namespace"),
        layout=_parse_layout_reference(table.get("layout"), f"{where}.layout"),
    )


def _parse_scopes(value: object, where: str) -> Mapping[str | None, Scope]:
    table = _table(value, where, none_as_empty=True)
    scopes: dict[str | None, Scope] = {}
    default: dict[str, object] = {}
    default_fields = {"description", "target_kind", "ignore", "namespace", "layout"}

    for raw_key, raw_value in table.items():
        if raw_key in default_fields and not isinstance(raw_value, dict):
            default[raw_key] = raw_value
            continue
        if not isinstance(raw_value, dict):
            if raw_key == "path":
                raise ConfigurationError(f"{where}.path: unnamed [scope] must not define path")
            raise ConfigurationError(f"{where}: unknown key: {raw_key}")

        name = _validate_scope_name(raw_key, where)
        scope_where = f"{where}.{name}"
        scopes[name] = _parse_scope(cast(dict[str, object], raw_value), scope_where, name=name)

    scopes[None] = _parse_scope(default, where, name=None)
    return MappingProxyType(scopes)


def _parse_fixed_sources(
    value: object,
    where: str,
    *,
    validate_name: Callable[[object, str], str],
    name_label: str,
    compatibility_namespace: bool,
) -> Mapping[str, Always]:
    if value is None:
        return MappingProxyType({})
    table = _table(value, where)
    sources: dict[str, Always] = {}
    source_names: dict[str, str] = {}
    for raw_name, raw_source in table.items():
        name = validate_name(raw_name, where)
        _require_distinct_casefold(name, source_names, where, label=name_label)
        source_where = f"{where}.{name}"
        raw_table = _table(raw_source, source_where)
        if compatibility_namespace:
            source_table, raw_namespace, uses_legacy_namespace = split_always_namespace(raw_table)
        else:
            source_table, raw_namespace, uses_legacy_namespace = raw_table, None, False
        _require_only_keys(
            source_table,
            {"path", "description", "must", "may", "ignore", "allow_empty", "layout"},
            source_where,
        )
        raw_path = source_table.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{source_where}.path: expected a string")
        path = validate_filesystem_location(raw_path, f"{source_where}.path", label="source path")
        selection = _parse_selection(
            {key: item for key, item in source_table.items() if key not in {"path", "layout"}},
            source_where,
        )
        namespace = (
            _parse_namespace_reference(raw_namespace, f"{source_where}.namespace")
            if uses_legacy_namespace
            else None
        )
        if namespace is not None:
            warn_always_namespace(source_where, namespace=namespace, source_name=name)
        sources[name] = Always(
            path=path,
            selection=selection,
            compatibility_namespace=namespace,
            layout=_parse_layout_reference(source_table.get("layout"), f"{source_where}.layout"),
        )
    return MappingProxyType(sources)


def _parse_always(value: object, where: str) -> Mapping[str, Always]:
    return _parse_fixed_sources(
        value,
        where,
        validate_name=_validate_always_name,
        name_label="Always source names",
        compatibility_namespace=True,
    )


def _parse_extras(value: object, where: str) -> Mapping[str, Always]:
    return _parse_fixed_sources(
        value,
        where,
        validate_name=_validate_extra_name,
        name_label="Extra source names",
        compatibility_namespace=False,
    )


def _parse_always_case_names(value: object, where: str) -> tuple[str, ...] | None:
    if value is None:
        return None
    try:
        items = _array(value, where)
    except ConfigurationError as exc:
        raise ConfigurationError(
            f"{where}: expected an array of Always/Extra source names"
        ) from exc
    names: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or not item.strip():
            raise ConfigurationError(f"{where}[{index}]: expected a non-empty string")
        names.append(item)
    if len(set(names)) != len(names):
        raise ConfigurationError(f"{where}: duplicate Always/Extra source names are not allowed")
    return tuple(names)


def _parse_always_cases(value: object, where: str) -> Mapping[str, AlwaysCase]:
    if value is None:
        return MappingProxyType({})
    table = _table(value, where)
    if not table:
        raise ConfigurationError(f"{where}: define at least one named case")

    cases: dict[str, AlwaysCase] = {}
    for raw_name, raw_case in table.items():
        name = _require_name(raw_name, where)
        if "." in name:
            raise ConfigurationError(
                f"{where}: case names must be flat and must not contain '.': {name!r}"
            )
        case_where = f"{where}.{name}"
        case_table = _table(raw_case, case_where)
        _require_only_keys(case_table, {"description", "include", "add", "exclude"}, case_where)
        if "include" in case_table and ("add" in case_table or "exclude" in case_table):
            raise ConfigurationError(
                f"{case_where}: include is mutually exclusive with add and exclude"
            )
        description = _description(case_table, case_where)
        include = _parse_always_case_names(case_table.get("include"), f"{case_where}.include")
        add = _parse_always_case_names(case_table.get("add"), f"{case_where}.add")
        exclude = _parse_always_case_names(case_table.get("exclude"), f"{case_where}.exclude")
        cases[name] = AlwaysCase(description=description, include=include, add=add, exclude=exclude)
    return MappingProxyType(cases)


def _parse_case_table(
    value: object, where: str
) -> tuple[Mapping[str, SelectionDefinition], Mapping[str, AlwaysCase]]:
    if value is None:
        return MappingProxyType({}), MappingProxyType({})
    table = _table(value, where)
    _require_only_keys(table, {"pluck", "always"}, where)
    if not table:
        raise ConfigurationError(f"{where}: define [case.pluck.<name>] and/or [case.always.<name>]")
    return (
        _parse_cases(table.get("pluck"), f"{where}.pluck"),
        _parse_always_cases(table.get("always"), f"{where}.always"),
    )


def _parse_about(
    value: object, where: str
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
    str | None,
]:
    if value is None:
        return None, None, None, None, None, None, None
    table = _table(value, where)
    _require_only_keys(
        table,
        {
            "description",
            "description_no_targets",
            "description_no_always",
            "description_empty",
            "always_layout",
            "targets_layout",
            "base",
        },
        where,
    )
    if not table:
        raise ConfigurationError(f"{where}: define at least one supported field")
    description = _description(table, where)
    description_no_targets = _description_field(table, "description_no_targets", where)
    description_no_always = _description_field(table, "description_no_always", where)
    description_empty = _description_field(table, "description_empty", where)
    always_layout = _parse_layout_reference(table.get("always_layout"), f"{where}.always_layout")
    targets_layout = _parse_layout_reference(table.get("targets_layout"), f"{where}.targets_layout")
    base = _validate_base_path(table["base"], f"{where}.base") if "base" in table else None
    return (
        description,
        description_no_targets,
        description_no_always,
        description_empty,
        always_layout,
        targets_layout,
        base,
    )


def _parse_output(value: object, where: str) -> Output | None:
    if value is None:
        return None
    table = _table(value, where)
    _require_only_keys(table, {"path", "overwrite", "timestamp"}, where)

    if "timestamp" in table:
        if "path" in table or "overwrite" in table:
            raise ConfigurationError(
                f"{where}: fixed output fields and [output.timestamp] are mutually exclusive"
            )
        raw_timestamp = table["timestamp"]
        timestamp_table = _table(raw_timestamp, f"{where}.timestamp")
        _require_only_keys(timestamp_table, {"path", "prefix", "suffix"}, f"{where}.timestamp")
        raw_path = timestamp_table.get("path")
        if not isinstance(raw_path, str):
            raise ConfigurationError(f"{where}.timestamp.path: expected a string")
        if not raw_path.endswith("/"):
            raise ConfigurationError(
                f"{where}.timestamp.path: timestamp output directory path must end with '/'"
            )
        path = validate_filesystem_location(
            raw_path, f"{where}.timestamp.path", label="output directory"
        )
        prefix = _validate_output_fragment(
            timestamp_table.get("prefix"), f"{where}.timestamp.prefix"
        )
        suffix = _validate_output_fragment(
            timestamp_table.get("suffix"), f"{where}.timestamp.suffix"
        )
        return Output(path=path, timestamp=True, prefix=prefix, suffix=suffix)

    raw_path = table.get("path")
    if not isinstance(raw_path, str):
        raise ConfigurationError(f"{where}.path: expected a string")
    if raw_path.endswith("/"):
        raise ConfigurationError(
            f"{where}.path: fixed output path must include a filename and must not end with '/'"
        )
    path = validate_filesystem_location(raw_path, f"{where}.path", label="output path")
    final_component = raw_path.rsplit("/", 1)[-1]
    if final_component in {".", ".."} or PurePosixPath(path) == PurePosixPath("."):
        raise ConfigurationError(f"{where}.path: output path must name a file")
    overwrite = table.get("overwrite", False)
    if not isinstance(overwrite, bool):
        raise ConfigurationError(f"{where}.overwrite: expected a boolean")
    return Output(path=path, overwrite=overwrite)


def load_config(path: str | Path = CONFIG_NAME) -> Config:
    """Load one dirpluck Configuration document without resolving its base chain."""

    manifest = lexical_absolute_path(Path(path).expanduser())
    if manifest.suffix != CONFIG_SUFFIX:
        raise ConfigurationError(f"configuration file must end with {CONFIG_SUFFIX!r}: {manifest}")
    data = _read_toml(manifest)
    _require_only_keys(
        data,
        {
            "about",
            "shared",
            "pluck",
            "case",
            "scope",
            "always",
            "extra",
            "namespace",
            "layout",
            "output",
        },
        str(manifest),
    )

    (
        about_description,
        about_description_no_targets,
        about_description_no_always,
        about_description_empty,
        about_always_layout,
        about_targets_layout,
        base,
    ) = _parse_about(data.get("about"), f"{manifest} [about]")
    shared = _parse_shared(data.get("shared"), f"{manifest} [shared]")
    raw_pluck, raw_legacy_cases, uses_legacy_pluck = split_legacy_pluck_table(data.get("pluck"))
    pluck = _parse_pluck(raw_pluck, f"{manifest} [pluck]")
    canonical_pluck_cases, always_cases = _parse_case_table(data.get("case"), f"{manifest} [case]")
    legacy_pluck_cases = _parse_cases(raw_legacy_cases, f"{manifest} [pluck].case")
    conflicts = sorted(set(legacy_pluck_cases) & set(canonical_pluck_cases))
    if conflicts:
        listed = ", ".join(repr(name) for name in conflicts)
        raise ConfigurationError(
            f"{manifest}: Pluck Case(s) are defined using both [pluck.case.<name>] and "
            + f"[case.pluck.<name>]: {listed}; use only [case.pluck.<name>]"
        )
    merged_pluck_cases = dict(legacy_pluck_cases)
    merged_pluck_cases.update(canonical_pluck_cases)
    if data.get("pluck") is not None and pluck is None and not merged_pluck_cases:
        raise ConfigurationError(
            f"{manifest} [pluck]: define the default pluck or at least one [case.pluck.<name>]"
        )
    pluck_cases = MappingProxyType(merged_pluck_cases)
    scopes = _parse_scopes(
        data.get("scope"),
        f"{manifest} [scope]",
    )
    always = _parse_always(data.get("always"), f"{manifest} [always]")
    extras = _parse_extras(data.get("extra"), f"{manifest} [extra]")
    namespaces = _parse_namespaces(data.get("namespace"), f"{manifest} [namespace]")
    layouts = _parse_layouts(data.get("layout"), f"{manifest} [layout]")
    output = _parse_output(data.get("output"), f"{manifest} [output]")

    config = Config(
        manifest=manifest,
        about_description=about_description,
        about_description_no_targets=about_description_no_targets,
        about_description_no_always=about_description_no_always,
        about_description_empty=about_description_empty,
        about_always_layout=about_always_layout,
        about_targets_layout=about_targets_layout,
        base=base,
        shared=shared,
        pluck=pluck,
        pluck_cases=pluck_cases,
        scopes=scopes,
        always=always,
        extras=extras,
        always_cases=always_cases,
        namespaces=namespaces,
        layouts=layouts,
        output=output,
    )
    if uses_legacy_pluck:
        warn_legacy_pluck_cases(manifest)
    if uses_legacy_selection_reference(data):
        warn_legacy_selection_references(manifest)
    return config

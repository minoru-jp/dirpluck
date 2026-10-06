"""Compile parsed Configuration documents into normalized runtime semantics."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Mapping
from types import MappingProxyType

from ._case import CaseSelection
from ._compatibility import CompatibilityNotice, always_layout_notice
from ._config_models import (
    Always,
    AlwaysCase,
    Config,
    Layout,
    SharedPatterns,
    Scope,
)
from ._selection_models import Selection
from ._selection_normalization import normalize_selection
from ._extraction_spec import BoundTargetSpec, ExtractionSpec, FixedSourceSpec, TargetRootSpec
from ._config_parser import load_config
from ._target_syntax import parse_target_reference
from .errors import ConfigurationError, SelectionError


@dataclass(frozen=True)
class CollectionPresentation:
    """Configuration-derived metadata consumed only by human-readable archive output."""

    about_description: str | None
    description_no_targets: str | None
    description_no_always: str | None
    description_empty: str | None
    layout_descriptions: Mapping[str, str | None]


def _resolve_base_config(config: Config) -> Config | None:
    if config.base is None:
        return None
    candidate = Path(config.base)
    if not candidate.is_absolute():
        candidate = config.manifest.parent / candidate
    try:
        return load_config(candidate)
    except ConfigurationError as exc:
        raise ConfigurationError(f"base Configuration is invalid: {exc}") from exc


def _configuration_chain(config: Config) -> tuple[Config, ...]:
    """Load one linear Base chain while detecting aliases of active documents."""

    layers: list[Config] = []
    active_manifests: list[Path] = []
    active_identities: list[Path] = []
    current = config
    while True:
        manifest = current.manifest
        identity = manifest.resolve(strict=True)
        if identity in active_identities:
            start = active_identities.index(identity)
            cycle = [*active_manifests[start:], manifest]
            rendered = " -> ".join(str(path) for path in cycle)
            raise ConfigurationError(f"Configuration base cycle detected: {rendered}")
        active_manifests.append(manifest)
        active_identities.append(identity)
        layers.append(current)
        next_config = _resolve_base_config(current)
        if next_config is None:
            break
        current = next_config
    return tuple(layers)


def _compose_shared(layers: tuple[Config, ...]) -> SharedPatterns:
    return SharedPatterns(
        must={
            name: patterns
            for config in reversed(layers)
            for name, patterns in config.shared.must.items()
        },
        may={
            name: patterns
            for config in reversed(layers)
            for name, patterns in config.shared.may.items()
        },
        ignore={
            name: patterns
            for config in reversed(layers)
            for name, patterns in config.shared.ignore.items()
        },
    )


def _compose_namespaces(layers: tuple[Config, ...]) -> frozenset[str]:
    return frozenset(name for config in layers for name in config.namespaces)


def _validate_namespace_names(namespaces: frozenset[str]) -> None:
    by_casefold: dict[str, str] = {}
    for name in namespaces:
        key = name.casefold()
        previous = by_casefold.get(key)
        if previous is not None:
            raise ConfigurationError(
                "effective Namespace names must be distinct ignoring case: "
                + f"{previous!r} and {name!r}"
            )
        by_casefold[key] = name


def _compose_layouts(layers: tuple[Config, ...]) -> Mapping[str, Layout]:
    layouts = {
        name: layout for config in reversed(layers) for name, layout in config.layouts.items()
    }
    by_casefold: dict[str, str] = {}
    for name in layouts:
        key = name.casefold()
        previous = by_casefold.get(key)
        if previous is not None:
            raise ConfigurationError(
                "effective Layout names must be distinct ignoring case: "
                + f"{previous!r} and {name!r}"
            )
        by_casefold[key] = name
    return MappingProxyType(layouts)


def _validate_layout_reference(
    layout: str | None,
    layouts: Mapping[str, Layout],
    *,
    where: str,
) -> None:
    if layout is not None and layout not in layouts:
        raise ConfigurationError(f"effective {where} references unknown Layout {layout!r}")


def _anchor_scope_root(config: Config, *, name: str | None, path: str | None) -> Path:
    base = config.manifest.parent
    candidate = base if name is None else Path(path or "")
    if name is not None and not candidate.is_absolute():
        candidate = base / candidate
    # Scope roots are only anchored here. Host filesystem alias resolution and
    # existence/type validation belong to the resolution phase when the Scope
    # is actually used.
    return Path(os.path.abspath(candidate))


def _anchor_always_root(config: Config, source: Always) -> Path:
    candidate = Path(source.path)
    if not candidate.is_absolute():
        candidate = config.manifest.parent / candidate
    # Preserve filesystem aliases for the explicitly configured Selection root;
    # nested traversal still rejects link-like entries later during extraction.
    return Path(os.path.abspath(candidate))


def _compose_pluck(
    layers: tuple[Config, ...], shared: SharedPatterns
) -> tuple[Selection | None, Mapping[str, Selection]]:
    default_definition = next((config.pluck for config in layers if config.pluck is not None), None)
    case_definitions = {
        name: definition
        for config in reversed(layers)
        for name, definition in config.pluck_cases.items()
    }

    default = (
        None
        if default_definition is None
        else normalize_selection(default_definition, shared, "[pluck]")
    )
    cases = {
        name: normalize_selection(definition, shared, f"[case.pluck.{name}]")
        for name, definition in case_definitions.items()
    }
    return default, cases


def _compose_scopes(
    layers: tuple[Config, ...],
    namespaces: frozenset[str],
    layouts: Mapping[str, Layout],
    default_layout: str | None,
) -> Mapping[str | None, TargetRootSpec]:
    root = layers[0]
    definitions: dict[str | None, tuple[Config, Scope]] = {None: (root, root.scopes[None])}
    for config in reversed(layers):
        for name, scope in config.scopes.items():
            if name is not None:
                definitions[name] = (config, scope)

    compiled: dict[str | None, TargetRootSpec] = {}
    for name, (owner, raw_scope) in definitions.items():
        scope = raw_scope
        where = "[scope]" if name is None else f"[scope.{name}]"
        if scope.namespace is not None and scope.namespace not in namespaces:
            raise ConfigurationError(
                f"effective {where}.namespace references unknown Namespace {scope.namespace!r}"
            )
        effective_layout = scope.layout if scope.layout is not None else default_layout
        _validate_layout_reference(effective_layout, layouts, where=f"{where}.layout")
        if scope.namespace is not None and effective_layout is not None:
            raise ConfigurationError(
                f"effective {where} cannot use both Namespace {scope.namespace!r} "
                + f"and Layout {effective_layout!r}"
            )
        compiled[name] = TargetRootSpec(
            name=name,
            label="unnamed Scope" if name is None else f"Scope {name!r}",
            root=_anchor_scope_root(owner, name=name, path=scope.path),
            description=scope.description,
            target_kind=scope.target_kind,
            ignore=scope.ignore,
            archive_prefix=effective_layout if effective_layout is not None else scope.namespace,
            layout_name=effective_layout,
        )
    return compiled


def _compose_fixed_sources(
    definitions: Mapping[str, tuple[Config, Always]],
    shared: SharedPatterns,
    namespaces: frozenset[str],
    layouts: Mapping[str, Layout],
    default_layout: str | None,
    *,
    table_name: str,
    compatibility_notices: bool,
) -> tuple[Mapping[str, FixedSourceSpec], Mapping[str, CompatibilityNotice]]:
    compiled: dict[str, FixedSourceSpec] = {}
    notices: dict[str, CompatibilityNotice] = {}
    archive_roots: dict[str, str] = {}
    for name, (owner, source) in definitions.items():
        where = f"[{table_name}.{name}]"
        if (
            source.compatibility_namespace is not None
            and source.compatibility_namespace not in namespaces
        ):
            raise ConfigurationError(
                f"effective {where}.namespace references unknown Namespace "
                + repr(source.compatibility_namespace)
            )
        effective_layout = source.layout if source.layout is not None else default_layout
        _validate_layout_reference(effective_layout, layouts, where=f"{where}.layout")
        if source.compatibility_namespace is not None and effective_layout is not None:
            raise ConfigurationError(
                f"effective {where} cannot use both Namespace "
                + f"{source.compatibility_namespace!r} and Layout {effective_layout!r}"
            )
        effective_name = source.compatibility_namespace or name
        archive_root = (
            effective_name if effective_layout is None else f"{effective_layout}/{effective_name}"
        )
        key = archive_root.casefold()
        previous = archive_roots.get(key)
        if previous is not None:
            raise ConfigurationError(
                f"effective {table_name.capitalize()} source archive roots must be distinct "
                + "ignoring case after namespace resolution and Layout application: "
                + f"[{table_name}.{previous}] conflicts with {archive_root!r} "
                + f"from {where}"
            )
        archive_roots[key] = name
        root = _anchor_always_root(owner, source)
        compiled[name] = FixedSourceSpec(
            label=f"always source {effective_name!r}",
            archive_root=archive_root,
            root=root,
            selection=normalize_selection(source.selection, shared, where),
            layout_name=effective_layout,
        )
        if compatibility_notices:
            notice = always_layout_notice(
                manifest=owner.manifest,
                source_name=name,
                source_root=root,
                namespace=source.compatibility_namespace,
                effective_name=effective_name,
                layout=effective_layout,
            )
            if notice is not None:
                notices[name] = notice
    return compiled, notices


def _effective_fixed_source_definitions(
    layers: tuple[Config, ...],
) -> tuple[
    Mapping[str, tuple[Config, Always]],
    Mapping[str, tuple[Config, Always]],
]:
    always = {
        name: (config, source)
        for config in reversed(layers)
        for name, source in config.always.items()
    }
    extras = {
        name: (config, source)
        for config in reversed(layers)
        for name, source in config.extras.items()
    }
    by_casefold: dict[str, tuple[str, str]] = {}
    for table_name, definitions in (("always", always), ("extra", extras)):
        for name in definitions:
            key = name.casefold()
            previous = by_casefold.get(key)
            if previous is not None:
                previous_table, previous_name = previous
                raise ConfigurationError(
                    "effective Always and Extra source names must be distinct ignoring case: "
                    + f"[{previous_table}.{previous_name}] and [{table_name}.{name}]"
                )
            by_casefold[key] = (table_name, name)
    return MappingProxyType(always), MappingProxyType(extras)


def _compose_always_cases(
    layers: tuple[Config, ...],
    always: Mapping[str, FixedSourceSpec],
    extras: Mapping[str, FixedSourceSpec],
) -> Mapping[str, AlwaysCase]:
    cases = {
        name: definition
        for config in reversed(layers)
        for name, definition in config.always_cases.items()
    }

    selectable = set(always) | set(extras)
    always_names = set(always)
    for case_name, case in cases.items():
        if case.include is not None:
            unknown = [name for name in case.include if name not in selectable]
            if unknown:
                listed = ", ".join(repr(name) for name in unknown)
                raise ConfigurationError(
                    f"effective [case.always.{case_name}].include references undefined "
                    + f"Always source(s) or Extra source(s): {listed}"
                )
        if case.add is not None:
            unknown = [name for name in case.add if name not in extras]
            if unknown:
                listed = ", ".join(repr(name) for name in unknown)
                raise ConfigurationError(
                    f"effective [case.always.{case_name}].add references source(s) that are "
                    + f"not effective Extra sources: {listed}; add accepts Extra sources only"
                )
        if case.exclude is not None:
            unknown = [name for name in case.exclude if name not in always_names]
            if unknown:
                listed = ", ".join(repr(name) for name in unknown)
                raise ConfigurationError(
                    f"effective [case.always.{case_name}].exclude references source(s) that are "
                    + f"not effective Always sources: {listed}; exclude accepts Always sources only"
                )
    return MappingProxyType(cases)


def _selected_pluck(
    default: Selection | None,
    cases: Mapping[str, Selection],
    selection: CaseSelection,
) -> tuple[Selection | None, str | None]:
    if selection.pluck is not None:
        try:
            return cases[selection.pluck], None
        except KeyError as exc:
            available = ", ".join(sorted(cases)) or "(none)"
            raise SelectionError(
                f"target case {selection.pluck!r} is not defined; available target cases: {available}"
            ) from exc
    if default is not None:
        return default, None
    available = ", ".join(sorted(cases)) or "(none)"
    if not cases:
        return (
            None,
            "the effective Configuration does not define Pluck; directory TARGET must not be specified",
        )
    return (
        None,
        "the effective Configuration has no default [pluck]; "
        + f"specify --case TARGET_CASE (available target cases: {available})",
    )


def _selected_always(
    always: Mapping[str, FixedSourceSpec],
    extras: Mapping[str, FixedSourceSpec],
    cases: Mapping[str, AlwaysCase],
    selection: CaseSelection,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    always_names = tuple(always)
    extra_names: tuple[str, ...] = ()
    if selection.always is not None:
        try:
            definition = cases[selection.always]
        except KeyError as exc:
            available = ", ".join(sorted(cases)) or "(none)"
            raise SelectionError(
                f"always case {selection.always!r} is not defined; available always cases: {available}"
            ) from exc
        if definition.include is not None:
            included = set(definition.include)
            always_names = tuple(name for name in always_names if name in included)
            extra_names = tuple(name for name in extras if name in included)
        else:
            if definition.exclude is not None:
                excluded = set(definition.exclude)
                always_names = tuple(name for name in always_names if name not in excluded)
            if definition.add is not None:
                added = set(definition.add)
                extra_names = tuple(name for name in extras if name in added)
    return always_names, extra_names


def compile_collection_input(
    config: Config,
    *,
    case: CaseSelection,
    target_references: tuple[str, ...],
) -> tuple[ExtractionSpec, CollectionPresentation, tuple[CompatibilityNotice, ...]]:
    """Compile Configuration semantics into extraction input and archive metadata."""

    layers = _configuration_chain(config)
    shared = _compose_shared(layers)
    namespaces = _compose_namespaces(layers)
    _validate_namespace_names(namespaces)
    layouts = _compose_layouts(layers)
    default_always_layout = next(
        (item.about_always_layout for item in layers if item.about_always_layout is not None),
        None,
    )
    default_targets_layout = next(
        (item.about_targets_layout for item in layers if item.about_targets_layout is not None),
        None,
    )
    _validate_layout_reference(default_always_layout, layouts, where="[about].always_layout")
    _validate_layout_reference(default_targets_layout, layouts, where="[about].targets_layout")

    pluck_default, pluck_cases = _compose_pluck(layers, shared)
    scopes = _compose_scopes(layers, namespaces, layouts, default_targets_layout)
    always_definitions, extra_definitions = _effective_fixed_source_definitions(layers)
    always, always_notices = _compose_fixed_sources(
        always_definitions,
        shared,
        namespaces,
        layouts,
        default_always_layout,
        table_name="always",
        compatibility_notices=True,
    )
    extras, _ = _compose_fixed_sources(
        extra_definitions,
        shared,
        namespaces,
        layouts,
        default_always_layout,
        table_name="extra",
        compatibility_notices=False,
    )
    always_cases = _compose_always_cases(layers, always, extras)
    directory_selection, directory_selection_error = _selected_pluck(
        pluck_default, pluck_cases, case
    )
    selected_always_names, selected_extra_names = _selected_always(
        always, extras, always_cases, case
    )
    compatibility_notices = tuple(
        notice for name in selected_always_names if (notice := always_notices.get(name)) is not None
    )
    presentation = CollectionPresentation(
        about_description=next(
            (item.about_description for item in layers if item.about_description is not None),
            None,
        ),
        description_no_targets=next(
            (
                item.about_description_no_targets
                for item in layers
                if item.about_description_no_targets is not None
            ),
            None,
        ),
        description_no_always=next(
            (
                item.about_description_no_always
                for item in layers
                if item.about_description_no_always is not None
            ),
            None,
        ),
        description_empty=next(
            (
                item.about_description_empty
                for item in layers
                if item.about_description_empty is not None
            ),
            None,
        ),
        layout_descriptions=MappingProxyType(
            {name: layout.description for name, layout in layouts.items()}
        ),
    )

    reference_count = len(target_references)
    target_expressions = tuple(
        (
            parse_target_reference(
                reference,
                scope_names=scopes.keys(),
                label=("target reference" if reference_count == 1 else f"target reference {index}"),
            ),
            "target reference" if reference_count == 1 else f"target reference {index}",
        )
        for index, reference in enumerate(target_references, start=1)
    )
    targets: list[BoundTargetSpec] = []
    for parsed, label in target_expressions:
        try:
            root = scopes[parsed.scope]
        except KeyError as exc:
            if parsed.scope is None:
                raise SelectionError("unnamed Scope is not defined") from exc
            raise SelectionError(f"Scope {parsed.scope!r} is not defined") from exc
        ignore_where = "[scope]" if parsed.scope is None else f"[scope.{parsed.scope}]"
        targets.append(
            BoundTargetSpec(
                expression=parsed.expression,
                root=root,
                label=label,
                ignore_where=ignore_where,
            )
        )

    return (
        ExtractionSpec(
            targets=tuple(targets),
            directory_selection=directory_selection,
            directory_selection_error=directory_selection_error,
            fixed_sources=(
                *(always[name] for name in selected_always_names),
                *(extras[name] for name in selected_extra_names),
            ),
        ),
        presentation,
        compatibility_notices,
    )

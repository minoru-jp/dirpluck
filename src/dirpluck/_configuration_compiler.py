"""Compile parsed Configuration documents into normalized runtime semantics."""

from __future__ import annotations

import os
from pathlib import Path
from collections.abc import Mapping

from ._case import CaseSelection
from ._compatibility import CompatibilityNotice, always_layout_notice
from ._config_models import (
    Always,
    AlwaysCase,
    Config,
    SharedPatterns,
    Scope,
)
from ._selection_models import Selection
from ._selection_normalization import normalize_selection
from ._extraction_spec import BoundTargetSpec, ExtractionSpec, FixedSourceSpec, TargetRootSpec
from ._config_parser import load_config
from ._target_syntax import parse_target_reference
from .errors import ConfigurationError, SelectionError


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
        if scope.namespace is not None and scope.namespace not in namespaces:
            where = "[scope]" if name is None else f"[scope.{name}]"
            raise ConfigurationError(
                f"effective {where}.namespace references unknown Namespace {scope.namespace!r}"
            )
        compiled[name] = TargetRootSpec(
            name=name,
            label="unnamed Scope" if name is None else f"Scope {name!r}",
            root=_anchor_scope_root(owner, name=name, path=scope.path),
            description=scope.description,
            target_kind=scope.target_kind,
            ignore=scope.ignore,
            archive_prefix=scope.namespace,
        )
    return compiled


def _compose_always(
    layers: tuple[Config, ...],
    shared: SharedPatterns,
    namespaces: frozenset[str],
) -> tuple[Mapping[str, FixedSourceSpec], Mapping[str, CompatibilityNotice]]:
    definitions = {
        name: (config, source)
        for config in reversed(layers)
        for name, source in config.always.items()
    }

    compiled: dict[str, FixedSourceSpec] = {}
    notices: dict[str, CompatibilityNotice] = {}
    archive_roots: dict[str, str] = {}
    for name, (owner, source) in definitions.items():
        if (
            source.compatibility_namespace is not None
            and source.compatibility_namespace not in namespaces
        ):
            raise ConfigurationError(
                f"effective [always.{name}].namespace references unknown Namespace "
                + repr(source.compatibility_namespace)
            )
        archive_root = source.compatibility_namespace or name
        key = archive_root.casefold()
        previous = archive_roots.get(key)
        if previous is not None:
            raise ConfigurationError(
                "effective Always source names must be distinct ignoring case after namespace resolution: "
                + f"[always.{previous}] resolves to a name that conflicts with {archive_root!r} "
                + f"from [always.{name}]"
            )
        archive_roots[key] = name
        root = _anchor_always_root(owner, source)
        compiled[name] = FixedSourceSpec(
            label=f"always source {archive_root!r}",
            archive_root=archive_root,
            root=root,
            selection=normalize_selection(source.selection, shared, f"[always.{name}]"),
        )
        notice = always_layout_notice(
            manifest=owner.manifest,
            source_name=name,
            source_root=root,
            namespace=source.compatibility_namespace,
            effective_name=archive_root,
        )
        if notice is not None:
            notices[name] = notice
    return compiled, notices


def _compose_always_cases(
    layers: tuple[Config, ...],
    always: Mapping[str, FixedSourceSpec],
) -> Mapping[str, AlwaysCase]:
    cases = {
        name: definition
        for config in reversed(layers)
        for name, definition in config.always_cases.items()
    }

    names = set(always)
    for case_name, case in cases.items():
        references = case.include if case.include is not None else case.exclude
        if references is None:
            continue
        unknown = [name for name in references if name not in names]
        if unknown:
            listed = ", ".join(repr(name) for name in unknown)
            raise ConfigurationError(
                f"effective [case.always.{case_name}] references undefined Always source(s): {listed}"
            )
    return cases


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
    cases: Mapping[str, AlwaysCase],
    selection: CaseSelection,
) -> tuple[str, ...]:
    names = tuple(always)
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
            names = tuple(name for name in names if name in included)
        elif definition.exclude is not None:
            excluded = set(definition.exclude)
            names = tuple(name for name in names if name not in excluded)
    return names


def compile_collection_input(
    config: Config,
    *,
    case: CaseSelection,
    target_references: tuple[str, ...],
) -> tuple[ExtractionSpec, str | None, tuple[CompatibilityNotice, ...]]:
    """Compile Configuration semantics into extraction input and archive metadata."""

    layers = _configuration_chain(config)
    shared = _compose_shared(layers)
    namespaces = _compose_namespaces(layers)
    _validate_namespace_names(namespaces)

    pluck_default, pluck_cases = _compose_pluck(layers, shared)
    scopes = _compose_scopes(layers, namespaces)
    always, always_notices = _compose_always(layers, shared, namespaces)
    always_cases = _compose_always_cases(layers, always)
    directory_selection, directory_selection_error = _selected_pluck(
        pluck_default, pluck_cases, case
    )
    selected_always_names = _selected_always(always, always_cases, case)
    compatibility_notices = tuple(
        notice for name in selected_always_names if (notice := always_notices.get(name)) is not None
    )
    about_description = next(
        (item.about_description for item in layers if item.about_description is not None),
        None,
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
            fixed_sources=tuple(always[name] for name in selected_always_names),
        ),
        about_description,
        compatibility_notices,
    )

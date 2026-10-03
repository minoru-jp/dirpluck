"""Composition and validation of layered effective Configurations."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping

from ._builder_models import (
    _AlwaysBinding,
    _ConfigurationLayer,
    _EffectiveConfiguration,
    _PluckBinding,
    _ScopeBinding,
)
from ._config_models import Config, ExclusionPattern, MatchPattern, Namespace, SharedPatterns
from ._config_values import _materialize_selection
from ._target_resolution import scope_label, scope_root_path
from .config import load_config
from .errors import ConfigurationError


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


def _configuration_chain(config: Config) -> tuple[_ConfigurationLayer, ...]:
    """Load one linear base chain and reject aliases of an active Configuration file."""

    layers: list[_ConfigurationLayer] = []
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
        layers.append(_ConfigurationLayer(current))
        next_config = _resolve_base_config(current)
        if next_config is None:
            break
        current = next_config
    return tuple(layers)


def _compose_shared(layers: tuple[_ConfigurationLayer, ...]) -> SharedPatterns:
    must: dict[str, tuple[str | MatchPattern, ...]] = {}
    may: dict[str, tuple[str | MatchPattern, ...]] = {}
    ignore: dict[str, tuple[ExclusionPattern | MatchPattern, ...]] = {}
    for layer in reversed(layers):
        must.update(layer.config.shared.must)
        may.update(layer.config.shared.may)
        ignore.update(layer.config.shared.ignore)
    return SharedPatterns(
        must=MappingProxyType(must),
        may=MappingProxyType(may),
        ignore=MappingProxyType(ignore),
    )


def _compose_namespaces(layers: tuple[_ConfigurationLayer, ...]) -> Mapping[str, Namespace]:
    namespaces: dict[str, Namespace] = {}
    for layer in reversed(layers):
        namespaces.update(layer.config.namespaces)
    return MappingProxyType(namespaces)


def _resolved_output_boundary(config: Config) -> tuple[str, Path] | None:
    output = config.output
    if output is None:
        return None
    candidate = Path(output.path)
    if not candidate.is_absolute():
        candidate = config.manifest.parent / candidate
    return ("timestamp" if output.timestamp else "fixed", candidate.resolve(strict=False))


def _path_contains(root: Path, path: Path) -> bool:
    try:
        _ = path.relative_to(root)
        return True
    except ValueError:
        return False


def _output_boundaries_overlap(left: tuple[str, Path], right: tuple[str, Path]) -> bool:
    left_kind, left_path = left
    right_kind, right_path = right
    if left_kind == "fixed" and right_kind == "fixed":
        return left_path == right_path
    if left_kind == "timestamp" and right_kind == "timestamp":
        return _path_contains(left_path, right_path) or _path_contains(right_path, left_path)
    if left_kind == "timestamp":
        return _path_contains(left_path, right_path)
    return _path_contains(right_path, left_path)


def _validate_output_boundaries(layers: tuple[_ConfigurationLayer, ...]) -> None:
    seen: list[tuple[_ConfigurationLayer, tuple[str, Path]]] = []
    for layer in layers:
        boundary = _resolved_output_boundary(layer.config)
        if boundary is None:
            continue
        for previous_layer, previous in seen:
            if _output_boundaries_overlap(boundary, previous):
                raise ConfigurationError(
                    "base chain Output write boundaries overlap: "
                    + f"{layer.config.manifest} -> {boundary[1]} and "
                    + f"{previous_layer.config.manifest} -> {previous[1]}"
                )
        seen.append((layer, boundary))


def _resolve_effective_scope_roots(effective: _EffectiveConfiguration) -> Mapping[str | None, Path]:
    roots: dict[str | None, Path] = {}
    by_root: dict[Path, str | None] = {}
    for name, binding in effective.scopes.items():
        # Duplicate detection is Configuration-level and must not require every
        # named Scope to be mounted or otherwise available in this run.
        root = scope_root_path(binding)
        previous_name = by_root.get(root)
        if previous_name is not None or root in by_root:
            raise ConfigurationError(
                f"effective Scope roots must be distinct: {scope_label(previous_name)} and {scope_label(name)} both resolve to {root}"
            )
        roots[name] = root
        by_root[root] = name
    return MappingProxyType(roots)


def _validate_pluck_selections(binding: _PluckBinding, shared: SharedPatterns) -> None:
    if binding.pluck.default is not None:
        _ = _materialize_selection(binding.pluck.default, shared, "[pluck]")
    for name, selection in binding.pluck.cases.items():
        _ = _materialize_selection(selection, shared, f"[pluck.case.{name}]")


def _validate_always_selections(binding: _AlwaysBinding, shared: SharedPatterns) -> None:
    source = binding.source
    _ = _materialize_selection(source.selection, shared, f"[always.{source.name}]")
    for name, selection in source.cases.items():
        _ = _materialize_selection(selection, shared, f"[always.{source.name}.case.{name}]")


def _validate_effective_configuration(effective: _EffectiveConfiguration) -> None:
    has_file_capable_scope = any(
        binding.scope.target_kind in {"file", "both"} for binding in effective.scopes.values()
    )
    if effective.pluck is None and not effective.always and not has_file_capable_scope:
        raise ConfigurationError(
            f"{effective.root.manifest}: the resolved Configuration chain defines no Pluck or Always source"
        )
    _ = _resolve_effective_scope_roots(effective)
    for scope_name, scope_binding in effective.scopes.items():
        namespace = scope_binding.scope.namespace
        if namespace is not None and namespace not in effective.namespaces:
            where = "[scope]" if scope_name is None else f"[scope.{scope_name}]"
            raise ConfigurationError(
                f"effective {where}.namespace references unknown Namespace {namespace!r}"
            )
    for always_name, always_binding in effective.always.items():
        namespace = always_binding.source.namespace
        if namespace is not None and namespace not in effective.namespaces:
            raise ConfigurationError(
                f"effective [always.{always_name}].namespace references unknown Namespace {namespace!r}"
            )
    if effective.pluck is not None:
        _validate_pluck_selections(effective.pluck, effective.shared)
        pluck_cases = set(effective.pluck.pluck.cases)
        for name, binding in effective.always.items():
            unreachable = sorted(set(binding.source.cases) - pluck_cases)
            if unreachable:
                listed = ", ".join(repr(case) for case in unreachable)
                raise ConfigurationError(
                    f"effective [always.{name}.case]: case(s) not defined by pluck: {listed}"
                )
    for binding in effective.always.values():
        _validate_always_selections(binding, effective.shared)


def compose_effective_configuration(config: Config) -> _EffectiveConfiguration:
    layers = _configuration_chain(config)
    _validate_output_boundaries(layers)
    about_description = next(
        (
            layer.config.about_description
            for layer in layers
            if layer.config.about_description is not None
        ),
        None,
    )
    shared = _compose_shared(layers)
    namespaces = _compose_namespaces(layers)

    pluck_binding = next(
        (
            _PluckBinding(layer.config.pluck, layer)
            for layer in layers
            if layer.config.pluck is not None
        ),
        None,
    )

    # The default Scope belongs to the root Configuration. Named Scopes compose
    # through the base chain by name.
    scopes: dict[str | None, _ScopeBinding] = {None: _ScopeBinding(config.scopes[None], layers[0])}
    always: dict[str, _AlwaysBinding] = {}
    for layer in reversed(layers):
        for name, scope in layer.config.scopes.items():
            if name is not None:
                scopes[name] = _ScopeBinding(scope, layer)
        for name, source in layer.config.always.items():
            always[name] = _AlwaysBinding(source, layer)

    effective = _EffectiveConfiguration(
        root=config,
        layers=layers,
        about_description=about_description,
        shared=shared,
        pluck=pluck_binding,
        scopes=MappingProxyType(scopes),
        always=MappingProxyType(always),
        namespaces=namespaces,
    )
    _validate_effective_configuration(effective)
    return effective

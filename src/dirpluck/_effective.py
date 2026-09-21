"""Effective Configuration composition and source resolution."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import Mapping
import os

from ._builder_common import _is_link_like
from ._builder_models import (
    BuildRequest,
    ResolvedSource,
    _AlwaysBinding,
    _ConfigurationLayer,
    _EffectiveConfiguration,
    _PluckBinding,
    _ScopeBinding,
)
from ._config_models import (
    Config,
    ExclusionPattern,
    Namespace,
    Selection,
    SharedPatterns,
    TargetIgnorePattern,
)
from ._config_values import _materialize_selection
from .config import load_config
from .errors import ConfigurationError, SelectionError


_RESERVED_ARCHIVE_ROOT_NAMES = frozenset({"readme.md"})


def _target_name_matches(name: str, pattern: TargetIgnorePattern) -> bool:
    if pattern.match == "exact":
        return name == pattern.value
    if pattern.match == "prefix":
        return name.startswith(pattern.value)
    if pattern.match == "suffix":
        return name.endswith(pattern.value)
    if pattern.match == "contains":
        return pattern.value in name
    raise AssertionError(f"unknown Scope ignore match kind: {pattern.match}")


def _target_is_ignored(name: str, patterns: tuple[TargetIgnorePattern, ...]) -> bool:
    return any(_target_name_matches(name, pattern) for pattern in patterns)


def _validate_target_name(name: str, *, label: str) -> None:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise SelectionError(f"{label} must name one direct child directory: {name!r}")


def _resolve_target_directory(name: str, root: Path, *, label: str) -> tuple[Path, str]:
    _validate_target_name(name, label=label)
    candidate = root / name
    if _is_link_like(candidate):
        raise SelectionError(
            f"{label} is a symbolic link or Windows junction and is not a selectable Target: {candidate}"
        )
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{label} does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise SelectionError(f"{label} is not a directory: {candidate}")
    root_resolved = root.resolve()
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SelectionError(f"{label} resolves outside its Scope root: {resolved}") from exc
    if len(relative.parts) != 1:
        raise SelectionError(f"{label} must resolve to a direct child directory of its Scope root: {resolved}")
    return resolved, relative.as_posix()


def _scope_label(name: str | None) -> str:
    return "unnamed Scope" if name is None else f"Scope {name!r}"


def _scope_root_path(binding: _ScopeBinding) -> Path:
    scope = binding.scope
    base = binding.layer.config.manifest.parent
    candidate = base if scope.name is None else Path(scope.path or "")
    if scope.name is not None and not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve(strict=False)


def _resolve_scope_root(binding: _ScopeBinding) -> Path:
    scope = binding.scope
    candidate = _scope_root_path(binding)
    if not candidate.exists():
        raise SelectionError(f"{_scope_label(scope.name)} root does not exist: {candidate}")
    if not candidate.is_dir():
        raise SelectionError(f"{_scope_label(scope.name)} root is not a directory: {candidate}")
    return candidate.resolve(strict=True)


def _target_reference_is_absolute(reference: str) -> bool:
    pure = PurePosixPath(reference)
    windows = PureWindowsPath(reference)
    return pure.is_absolute() or windows.is_absolute() or bool(windows.drive)


def _expand_scope(binding: _ScopeBinding) -> tuple[tuple[Path, str], ...]:
    root = _resolve_scope_root(binding)
    scope = binding.scope
    targets: list[tuple[Path, str]] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if _target_is_ignored(entry.name, scope.ignore):
            continue
        if _is_link_like(entry):
            continue
        if not entry.is_dir():
            continue
        targets.append(
            _resolve_target_directory(
                entry.name,
                root,
                label=f"target from {_scope_label(scope.name)}",
            )
        )
    if not targets:
        raise SelectionError(f"{_scope_label(scope.name)} contains no eligible direct child directories")
    return tuple(targets)


def _require_scope(effective: _EffectiveConfiguration, name: str | None) -> _ScopeBinding:
    try:
        return effective.scopes[name]
    except KeyError as exc:
        if name is None:
            raise SelectionError("unnamed Scope is not defined") from exc
        raise SelectionError(f"Scope {name!r} is not defined") from exc


def _resolve_target_reference(
    reference: str,
    effective: _EffectiveConfiguration,
    *,
    label: str,
) -> tuple[tuple[Path, str, str | None], ...]:
    if not reference:
        raise SelectionError(f"{label} must not be empty")
    if "\\" in reference:
        raise SelectionError(f"{label} must use '/' as the separator: {reference!r}")

    def from_scope(binding: _ScopeBinding, targets: tuple[tuple[Path, str], ...]) -> tuple[tuple[Path, str, str | None], ...]:
        return tuple((directory, source_root, binding.scope.namespace) for directory, source_root in targets)

    if reference == "/":
        binding = _require_scope(effective, None)
        return from_scope(binding, _expand_scope(binding))

    if _target_reference_is_absolute(reference):
        raise SelectionError(
            f"{label} must use NAME, SCOPE/NAME, '/', or SCOPE/: {reference!r}"
        )

    if reference.endswith("/"):
        scope_name = reference[:-1]
        _validate_target_name(scope_name, label="Scope name")
        binding = _require_scope(effective, scope_name)
        return from_scope(binding, _expand_scope(binding))

    parts = reference.split("/")
    if len(parts) == 1:
        name = parts[0]
        binding = _require_scope(effective, None)
        _validate_target_name(name, label=label)
        if _target_is_ignored(name, binding.scope.ignore):
            raise SelectionError(f"{label} is ignored by [scope].ignore: {name!r}")
        directory, source_root = _resolve_target_directory(
            name, _resolve_scope_root(binding), label=label
        )
        return ((directory, source_root, binding.scope.namespace),)

    if len(parts) == 2 and all(parts):
        scope_name, name = parts
        _validate_target_name(scope_name, label="Scope name")
        _validate_target_name(name, label=label)
        binding = _require_scope(effective, scope_name)
        if _target_is_ignored(name, binding.scope.ignore):
            raise SelectionError(f"{label} is ignored by [scope.{scope_name}].ignore: {name!r}")
        directory, source_root = _resolve_target_directory(
            name, _resolve_scope_root(binding), label=label
        )
        return ((directory, source_root, binding.scope.namespace),)

    raise SelectionError(f"{label} must use NAME, SCOPE/NAME, '/', or SCOPE/: {reference!r}")


def _archive_root(source_root: str, namespace: str | None) -> str:
    return source_root if namespace is None else f"{namespace}/{source_root}"


def _resolve_always_directory(binding: _AlwaysBinding) -> tuple[Path, str]:
    source = binding.source
    base = binding.layer.config.manifest.parent
    candidate = Path(source.path)
    if not candidate.is_absolute():
        candidate = base / candidate

    # The configured location is an explicit source root.  Filesystem aliases
    # may therefore be used to select that root; link-like entries encountered
    # later while traversing the selected tree remain non-selectable.
    location = Path(os.path.abspath(candidate))
    try:
        resolved = location.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"always source {source.name!r} does not exist: {location}") from exc
    if not resolved.is_dir():
        raise SelectionError(f"always source {source.name!r} is not a directory: {location}")
    if resolved.parent == resolved:
        raise SelectionError(f"always source {source.name!r} cannot use the filesystem root as a source directory")

    base_location = Path(os.path.abspath(base))
    try:
        relative = location.relative_to(base_location)
    except ValueError:
        return resolved, location.name
    if relative == Path("."):
        return resolved, location.name
    return resolved, relative.as_posix()


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
    must: dict[str, tuple[str, ...]] = {}
    may: dict[str, tuple[str, ...]] = {}
    ignore: dict[str, tuple[ExclusionPattern, ...]] = {}
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
        path.relative_to(root)
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
                    f"{layer.config.manifest} -> {boundary[1]} and "
                    f"{previous_layer.config.manifest} -> {previous[1]}"
                )
        seen.append((layer, boundary))


def _resolve_effective_scope_roots(effective: _EffectiveConfiguration) -> Mapping[str | None, Path]:
    roots: dict[str | None, Path] = {}
    by_root: dict[Path, str | None] = {}
    for name, binding in effective.scopes.items():
        # Duplicate detection is Configuration-level and must not require every
        # named Scope to be mounted or otherwise available in this run.
        root = _scope_root_path(binding)
        previous_name = by_root.get(root)
        if previous_name is not None or root in by_root:
            raise ConfigurationError(
                f"effective Scope roots must be distinct: {_scope_label(previous_name)} and {_scope_label(name)} both resolve to {root}"
            )
        roots[name] = root
        by_root[root] = name
    return MappingProxyType(roots)


def _validate_pluck_selections(binding: _PluckBinding, shared: SharedPatterns) -> None:
    if binding.pluck.default is not None:
        _materialize_selection(binding.pluck.default, shared, "[pluck]")
    for name, selection in binding.pluck.cases.items():
        _materialize_selection(selection, shared, f"[pluck.case.{name}]")


def _validate_always_selections(binding: _AlwaysBinding, shared: SharedPatterns) -> None:
    source = binding.source
    _materialize_selection(source.selection, shared, f"[always.{source.name}]")
    for name, selection in source.cases.items():
        _materialize_selection(selection, shared, f"[always.{source.name}.case.{name}]")


def _validate_effective_configuration(effective: _EffectiveConfiguration) -> None:
    if effective.pluck is None and not effective.always:
        raise ConfigurationError(f"{effective.root.manifest}: the resolved Configuration chain defines no Pluck or Always source")
    _resolve_effective_scope_roots(effective)
    for scope_name, scope_binding in effective.scopes.items():
        namespace = scope_binding.scope.namespace
        if namespace is not None and namespace not in effective.namespaces:
            where = "[scope]" if scope_name is None else f"[scope.{scope_name}]"
            raise ConfigurationError(f"effective {where}.namespace references unknown Namespace {namespace!r}")
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


def _compose_effective_configuration(config: Config) -> _EffectiveConfiguration:
    layers = _configuration_chain(config)
    _validate_output_boundaries(layers)
    about_description = next(
        (layer.config.about_description for layer in layers if layer.config.about_description is not None),
        None,
    )
    shared = _compose_shared(layers)
    namespaces = _compose_namespaces(layers)

    pluck_binding = next(
        (_PluckBinding(layer.config.pluck, layer) for layer in layers if layer.config.pluck is not None),
        None,
    )

    # The default Scope belongs to the root Configuration. Named Scopes compose
    # through the base chain by name.
    scopes: dict[str | None, _ScopeBinding] = {
        None: _ScopeBinding(config.scopes[None], layers[0])
    }
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


def _available_cases(effective: _EffectiveConfiguration) -> tuple[str, ...]:
    if effective.pluck is not None:
        return tuple(sorted(effective.pluck.pluck.cases))
    return tuple(sorted({case for binding in effective.always.values() for case in binding.source.cases}))


def _validate_request(effective: _EffectiveConfiguration, request: BuildRequest) -> None:
    if effective.pluck is None:
        if request.directories:
            raise SelectionError("the effective Configuration does not define Pluck; TARGET must not be specified")
    elif not request.directories:
        raise SelectionError("TARGET is required when the effective Configuration defines Pluck (one or more may be specified)")

    if request.case is None:
        return
    available = _available_cases(effective)
    if request.case not in available:
        listed = ", ".join(available) or "(none)"
        raise SelectionError(f"case {request.case!r} is not defined; available cases: {listed}")


def _selected_pluck(binding: _PluckBinding, case: str | None, *, shared: SharedPatterns) -> Selection:
    pluck = binding.pluck
    if case is None:
        if pluck.default is None:
            available = ", ".join(sorted(pluck.cases)) or "(none)"
            raise SelectionError(f"the effective Pluck has no default [pluck]; specify --case NAME (available: {available})")
        return _materialize_selection(pluck.default, shared, "[pluck]")
    try:
        selection = pluck.cases[case]
    except KeyError as exc:
        available = ", ".join(sorted(pluck.cases)) or "(none)"
        raise SelectionError(f"case {case!r} is not defined for pluck; available cases: {available}") from exc
    return _materialize_selection(selection, shared, f"[pluck.case.{case}]")


def _selected_always(binding: _AlwaysBinding, case: str | None, *, shared: SharedPatterns) -> Selection:
    source = binding.source
    if case is not None and case in source.cases:
        return _materialize_selection(source.cases[case], shared, f"[always.{source.name}.case.{case}]")
    return _materialize_selection(source.selection, shared, f"[always.{source.name}]")


def _validate_resolved_archive_roots(sources: tuple[ResolvedSource, ...]) -> None:
    by_root: dict[str, ResolvedSource] = {}
    for source in sources:
        first_component = PurePosixPath(source.archive_root).parts[0]
        if first_component.casefold() in _RESERVED_ARCHIVE_ROOT_NAMES:
            raise SelectionError(
                f"{source.label} resolves under reserved archive root {first_component!r}; "
                "dirpluck reserves root-level 'README.md' for the generated archive index"
            )
        previous = by_root.get(source.archive_root)
        if previous is not None:
            raise SelectionError(
                "resolved sources must have distinct archive roots: "
                f"{previous.label} and {source.label} both resolve to {source.archive_root!r}; "
                "assign a Namespace to one or both sources to keep them distinct"
            )
        by_root[source.archive_root] = source


def _resolve_effective_sources(effective: _EffectiveConfiguration, request: BuildRequest) -> tuple[ResolvedSource, ...]:
    _validate_request(effective, request)
    resolved: list[ResolvedSource] = []

    if effective.pluck is not None:
        selection = _selected_pluck(effective.pluck, request.case, shared=effective.shared)
        runtime_targets: list[tuple[Path, str, str | None]] = []
        seen: set[Path] = set()
        reference_count = len(request.directories)
        for index, requested in enumerate(request.directories, start=1):
            label = f"target reference {index}" if reference_count > 1 else "target reference"
            for directory, source_root, namespace in _resolve_target_reference(requested, effective, label=label):
                if directory in seen:
                    raise SelectionError(f"target directories must resolve to distinct directories: {directory}")
                seen.add(directory)
                runtime_targets.append((directory, source_root, namespace))
        target_count = len(runtime_targets)
        for index, (directory, source_root, namespace) in enumerate(runtime_targets, start=1):
            key = "target" if target_count == 1 else f"target:{index}"
            name = None if target_count == 1 else source_root
            resolved.append(
                ResolvedSource(
                    key=key,
                    kind="target",
                    name=name,
                    description=selection.description,
                    directory=directory,
                    source_root=source_root,
                    namespace=namespace,
                    archive_root=_archive_root(source_root, namespace),
                    selection=selection,
                )
            )

    for name, binding in effective.always.items():
        selection = _selected_always(binding, request.case, shared=effective.shared)
        directory, source_root = _resolve_always_directory(binding)
        namespace = binding.source.namespace
        resolved.append(
            ResolvedSource(
                key=f"always:{name}",
                kind="always",
                name=name,
                description=selection.description,
                directory=directory,
                source_root=source_root,
                namespace=namespace,
                archive_root=_archive_root(source_root, namespace),
                selection=selection,
            )
        )

    sources = tuple(resolved)
    _validate_resolved_archive_roots(sources)
    return sources


def _resolve_execution(config: Config, request: BuildRequest) -> tuple[_EffectiveConfiguration, tuple[ResolvedSource, ...]]:
    effective = _compose_effective_configuration(config)
    return effective, _resolve_effective_sources(effective, request)


def resolve_sources(config: Config, request: BuildRequest) -> tuple[ResolvedSource, ...]:
    """Resolve sources from one layered Effective Configuration."""

    _, sources = _resolve_execution(config, request)
    return sources

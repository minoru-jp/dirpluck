"""Effective Configuration orchestration and source resolution."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
import os

from ._builder_models import (
    BuildRequest,
    ResolvedSource,
    _AlwaysBinding,
    _EffectiveConfiguration,
    _PluckBinding,
)
from ._config_models import Config, Selection, SharedPatterns
from ._config_values import _materialize_selection
from ._configuration_composition import compose_effective_configuration
from ._target_resolution import resolve_target_reference, target_selector_binding
from .errors import SelectionError


_RESERVED_ARCHIVE_ROOT_NAMES = frozenset({"readme.md"})


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
        raise SelectionError(
            f"always source {source.name!r} cannot use the filesystem root as a source directory"
        )

    base_location = Path(os.path.abspath(base))
    try:
        relative = location.relative_to(base_location)
    except ValueError:
        return resolved, location.name
    if relative == Path("."):
        return resolved, location.name
    return resolved, relative.as_posix()


def _available_cases(effective: _EffectiveConfiguration) -> tuple[str, ...]:
    if effective.pluck is not None:
        return tuple(sorted(effective.pluck.pluck.cases))
    return tuple(
        sorted({case for binding in effective.always.values() for case in binding.source.cases})
    )


def _validate_request(effective: _EffectiveConfiguration, request: BuildRequest) -> None:
    if effective.pluck is not None and not request.directories:
        raise SelectionError(
            "TARGET is required when the effective Configuration defines Pluck (one or more may be specified)"
        )
    if effective.pluck is None and not effective.always and not request.directories:
        raise SelectionError(
            "TARGET is required when the effective Configuration only defines file-capable Target Scopes"
        )

    if request.case is None:
        return
    available = _available_cases(effective)
    if request.case not in available:
        listed = ", ".join(available) or "(none)"
        raise SelectionError(f"case {request.case!r} is not defined; available cases: {listed}")


def _selected_pluck(
    binding: _PluckBinding, case: str | None, *, shared: SharedPatterns
) -> Selection:
    pluck = binding.pluck
    if case is None:
        if pluck.default is None:
            available = ", ".join(sorted(pluck.cases)) or "(none)"
            raise SelectionError(
                f"the effective Pluck has no default [pluck]; specify --case NAME (available: {available})"
            )
        return _materialize_selection(pluck.default, shared, "[pluck]")
    try:
        selection = pluck.cases[case]
    except KeyError as exc:
        available = ", ".join(sorted(pluck.cases)) or "(none)"
        raise SelectionError(
            f"case {case!r} is not defined for pluck; available cases: {available}"
        ) from exc
    return _materialize_selection(selection, shared, f"[pluck.case.{case}]")


def _selected_always(
    binding: _AlwaysBinding, case: str | None, *, shared: SharedPatterns
) -> Selection:
    source = binding.source
    if case is not None and case in source.cases:
        return _materialize_selection(
            source.cases[case], shared, f"[always.{source.name}.case.{case}]"
        )
    return _materialize_selection(source.selection, shared, f"[always.{source.name}]")


def _validate_resolved_archive_roots(sources: tuple[ResolvedSource, ...]) -> None:
    by_root: dict[str, ResolvedSource] = {}
    for source in sources:
        first_component = PurePosixPath(source.archive_root).parts[0]
        if first_component.casefold() in _RESERVED_ARCHIVE_ROOT_NAMES:
            raise SelectionError(
                f"{source.label} resolves under reserved archive root {first_component!r}; "
                + "dirpluck reserves root-level 'README.md' for the generated archive index"
            )
        previous = by_root.get(source.archive_root)
        if previous is not None:
            raise SelectionError(
                "resolved sources must have distinct archive roots: "
                + f"{previous.label} and {source.label} both resolve to {source.archive_root!r}; "
                + "assign a Namespace to one or both sources to keep them distinct"
            )
        by_root[source.archive_root] = source


def _resolve_effective_sources(
    effective: _EffectiveConfiguration, request: BuildRequest
) -> tuple[ResolvedSource, ...]:
    _validate_request(effective, request)
    resolved: list[ResolvedSource] = []

    runtime_targets: list[tuple[Path, str, str | None, str, str | None]] = []
    seen: set[Path] = set()
    seen_from_selector: set[Path] = set()
    reference_count = len(request.directories)
    for index, requested in enumerate(request.directories, start=1):
        label = f"target reference {index}" if reference_count > 1 else "target reference"
        is_selector = target_selector_binding(requested, effective) is not None
        for (
            path,
            source_root,
            namespace,
            source_kind,
            scope_description,
        ) in resolve_target_reference(requested, effective, label=label):
            if path in seen:
                if is_selector or path in seen_from_selector:
                    continue
                raise SelectionError(f"targets must resolve to distinct filesystem entries: {path}")
            seen.add(path)
            if is_selector:
                seen_from_selector.add(path)
            runtime_targets.append((path, source_root, namespace, source_kind, scope_description))

    directory_selection: Selection | None = None
    if any(source_kind == "directory" for _, _, _, source_kind, _ in runtime_targets):
        if effective.pluck is None:
            raise SelectionError(
                "the effective Configuration does not define Pluck; TARGET must not be specified"
            )
        directory_selection = _selected_pluck(
            effective.pluck, request.case, shared=effective.shared
        )

    target_count = len(runtime_targets)
    for index, (path, source_root, namespace, source_kind, scope_description) in enumerate(
        runtime_targets, start=1
    ):
        key = "target" if target_count == 1 else f"target:{index}"
        name = None if target_count == 1 else source_root
        if source_kind == "directory":
            if directory_selection is None:
                raise AssertionError("directory Target has no effective Pluck Selection")
            selection = directory_selection
            description = selection.description
        else:
            selection = None
            description = None
        resolved.append(
            ResolvedSource(
                key=key,
                kind="target",
                name=name,
                description=description,
                scope_description=scope_description,
                source_kind=source_kind,
                directory=path,
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
                scope_description=None,
                source_kind="directory",
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


def _resolve_execution(
    config: Config, request: BuildRequest
) -> tuple[_EffectiveConfiguration, tuple[ResolvedSource, ...]]:
    effective = compose_effective_configuration(config)
    return effective, _resolve_effective_sources(effective, request)


def resolve_sources(config: Config, request: BuildRequest) -> tuple[ResolvedSource, ...]:
    """Resolve sources from one layered Effective Configuration."""

    _, sources = _resolve_execution(config, request)
    return sources

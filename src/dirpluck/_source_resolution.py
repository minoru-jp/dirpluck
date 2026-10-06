"""Resolve normalized Targets and fixed sources to concrete filesystem roots."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from ._resolution_models import ResolvedSource, ResolvedTarget
from ._extraction_spec import ExtractionSpec, FixedSourceSpec
from ._target_resolution import resolve_target_expression
from .errors import SelectionError


_RESERVED_ARCHIVE_ROOT_NAMES = frozenset({"readme.md"})


def _resolve_fixed_directory(source: FixedSourceSpec) -> Path:
    # The configured location is an explicit Selection root. Filesystem aliases
    # may therefore be used to select that root; nested traversal still rejects
    # link-like entries later during file collection.
    try:
        resolved = source.root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{source.label} does not exist: {source.root}") from exc
    if not resolved.is_dir():
        raise SelectionError(f"{source.label} is not a directory: {source.root}")
    return resolved


def _validate_resolved_archive_roots(sources: tuple[ResolvedSource, ...]) -> None:
    roots: dict[str, ResolvedSource] = {}
    for source in sources:
        first_component = PurePosixPath(source.archive_root).parts[0]
        if first_component.casefold() in _RESERVED_ARCHIVE_ROOT_NAMES:
            raise SelectionError(
                f"{source.label} resolves under reserved archive root {first_component!r}; "
                + "dirpluck reserves root-level 'README.md' for the generated archive index"
            )

        root_key = source.archive_root.casefold()
        previous = roots.get(root_key)
        if previous is not None:
            if previous.archive_root != source.archive_root:
                raise SelectionError(
                    "resolved sources have archive roots that differ only by case: "
                    + f"{previous.label} resolves to {previous.archive_root!r} and "
                    + f"{source.label} resolves to {source.archive_root!r}; "
                    + "choose distinct archive roots"
                )
            raise SelectionError(
                "resolved sources must have distinct archive roots: "
                + f"{previous.label} and {source.label} both resolve to {source.archive_root!r}"
            )
        roots[root_key] = source


def resolve_normalized_sources(spec: ExtractionSpec) -> tuple[ResolvedSource, ...]:
    """Resolve one normalized execution against source filesystems."""

    resolved: list[ResolvedSource] = []
    runtime_targets: list[ResolvedTarget] = []
    seen: set[Path] = set()
    seen_from_selector: set[Path] = set()
    for bound_target in spec.targets:
        is_selector = bound_target.expression.selector
        for target in resolve_target_expression(bound_target):
            if target.path in seen:
                if is_selector or target.path in seen_from_selector:
                    continue
                raise SelectionError(
                    f"targets must resolve to distinct filesystem entries: {target.path}"
                )
            seen.add(target.path)
            if is_selector:
                seen_from_selector.add(target.path)
            runtime_targets.append(target)

    if any(target.source_kind == "directory" for target in runtime_targets):
        if spec.directory_selection is None:
            if spec.directory_selection_error is None:
                raise AssertionError("directory Target has no Selection or diagnostic")
            raise SelectionError(spec.directory_selection_error)

    target_count = len(runtime_targets)
    for index, target in enumerate(runtime_targets, start=1):
        key = "target" if target_count == 1 else f"target:{index}"
        label = "target" if target_count == 1 else f"target {target.source_root!r}"
        if target.source_kind == "directory":
            selection = spec.directory_selection
            if selection is None:
                raise AssertionError("directory Target has no normalized Pluck Selection")
            selection_description = selection.description
        else:
            selection = None
            selection_description = None
        resolved.append(
            ResolvedSource(
                key=key,
                role="target",
                label=label,
                source_kind=target.source_kind,
                directory=target.path,
                archive_root=target.archive_root,
                selection=selection,
                scope_name=target.scope_name,
                scope_description=target.scope_description,
                description=selection_description,
                layout_name=target.layout_name,
            )
        )

    for source in spec.fixed_sources:
        resolved.append(
            ResolvedSource(
                key=f"fixed:{source.archive_root}",
                role="fixed",
                label=source.label,
                source_kind="directory",
                directory=_resolve_fixed_directory(source),
                archive_root=source.archive_root,
                selection=source.selection,
                description=source.selection.description,
                layout_name=source.layout_name,
            )
        )

    sources = tuple(resolved)
    _validate_resolved_archive_roots(sources)
    return sources

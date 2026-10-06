"""Filesystem extraction and archive-path planning from normalized inputs."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

from ._extraction_models import (
    EmptySelectionStatus,
    ExtractedSource,
    ExtractionResult,
    MissingSelectionStatus,
    SelectionTypeMismatchStatus,
    TargetOverlapStatus,
)
from ._resolution_models import ResolvedSource
from ._extraction_spec import ExtractionSpec
from ._selection import select_files
from ._source_resolution import resolve_normalized_sources
from .errors import SelectionError


def _archive_path(source: ResolvedSource, file: Path) -> str:
    if source.source_kind == "file":
        return source.archive_root
    relative = file.relative_to(source.directory).as_posix()
    return f"{source.archive_root}/{relative}"


def _add_archive_entry(
    entries: dict[str, Path],
    atomic_file_paths: set[str],
    *,
    archive_path: str,
    source_file: Path,
    atomic: bool,
) -> None:
    """Add one selected file while preserving archive path collision semantics."""

    source_resolved = source_file.resolve()
    previous = entries.get(archive_path)
    if previous is not None and previous.resolve() != source_resolved:
        raise SelectionError(
            f"multiple files resolve to the same archive path {archive_path!r}: "
            + f"{previous} and {source_file}"
        )

    conflict_candidates = entries if atomic else atomic_file_paths
    for existing in conflict_candidates:
        if existing == archive_path:
            continue
        if existing.startswith(archive_path + "/") or archive_path.startswith(existing + "/"):
            raise SelectionError(
                "archive file/directory path conflict between "
                + f"{existing!r} and {archive_path!r}"
            )

    entries[archive_path] = source_file
    if atomic:
        atomic_file_paths.add(archive_path)


def extract(
    spec: ExtractionSpec,
    *,
    allow_missing: bool = False,
) -> ExtractionResult:
    """Collect files and determine exact archive-path semantics."""

    sources = resolve_normalized_sources(spec)

    archive_entries: dict[str, Path] = {}
    atomic_file_paths: set[str] = set()
    selected_physical_entries: dict[str, set[Path]] = {}
    missing_entries: list[str] = []
    optional_missing_entries: list[str] = []
    empty_selections: list[EmptySelectionStatus] = []
    missing_selections: list[MissingSelectionStatus] = []
    type_mismatches: list[SelectionTypeMismatchStatus] = []
    selection_counts: dict[str, int] = {}
    skipped_links: set[Path] = set()

    for source in sources:
        result = select_files(source, allow_missing=allow_missing)
        skipped_links.update(result.skipped_links)
        type_mismatches.extend(result.type_mismatches)
        selection_counts[source.key] = len(result.files)
        selected_physical_entries[source.key] = {file.resolve() for file in result.files}
        opaque_missing = set(result.opaque_missing)
        opaque_optional_missing = set(result.opaque_optional_missing)
        missing_entries.extend(
            f"{source.archive_root}/{relative}"
            for relative in result.missing
            if relative not in opaque_missing
        )
        optional_missing_entries.extend(
            f"{source.archive_root}/{relative}"
            for relative in result.optional_missing
            if relative not in opaque_optional_missing
        )
        missing_selections.extend(
            MissingSelectionStatus(
                source_label=source.label,
                archive_root=source.archive_root,
                expression=expression,
                optional=False,
            )
            for expression in result.opaque_missing
        )
        missing_selections.extend(
            MissingSelectionStatus(
                source_label=source.label,
                archive_root=source.archive_root,
                expression=expression,
                optional=True,
            )
            for expression in result.opaque_optional_missing
        )

        if not result.files:
            if source.selection is None:
                raise AssertionError(f"atomic file source selected no file: {source.label}")
            empty_selections.append(
                EmptySelectionStatus(
                    key=source.key,
                    label=source.label,
                    archive_root=source.archive_root,
                    allow_empty=source.selection.allow_empty,
                )
            )
            if not source.selection.allow_empty and not allow_missing:
                raise SelectionError(f"{source.label} selected no files and allow_empty is false")

        for file in result.files:
            _add_archive_entry(
                archive_entries,
                atomic_file_paths,
                archive_path=_archive_path(source, file),
                source_file=file,
                atomic=source.source_kind == "file",
            )

    empty_directories = sorted(
        {
            status.archive_root
            for status in empty_selections
            if status.allow_empty
            and not any(
                arcname.startswith(f"{status.archive_root}/") for arcname in archive_entries
            )
        }
    )
    targets = tuple(source for source in sources if source.role == "target")
    target_overlaps: dict[str, tuple[TargetOverlapStatus, ...]] = {}
    for source in sources:
        if source.role != "fixed":
            continue
        overlaps: list[TargetOverlapStatus] = []
        source_entries = selected_physical_entries[source.key]
        for target in targets:
            count = len(source_entries & selected_physical_entries[target.key])
            if count:
                overlaps.append(
                    TargetOverlapStatus(
                        archive_root=target.archive_root,
                        source_kind=target.source_kind,
                        count=count,
                    )
                )
        if overlaps:
            target_overlaps[source.key] = tuple(
                sorted(overlaps, key=lambda item: (item.archive_root, item.source_kind))
            )

    extracted_sources = tuple(
        ExtractedSource(
            key=source.key,
            role=source.role,
            archive_root=source.archive_root,
            source_kind=source.source_kind,
            source_path=source.directory,
            description=source.description,
            selected_count=selection_counts[source.key],
            layout_name=source.layout_name,
            scope_name=source.scope_name,
            scope_description=source.scope_description,
            target_overlaps=target_overlaps.get(source.key, ()),
        )
        for source in sources
    )

    return ExtractionResult(
        sources=extracted_sources,
        entries=MappingProxyType(dict(sorted(archive_entries.items()))),
        missing=tuple(sorted(set(missing_entries))),
        optional_missing=tuple(sorted(set(optional_missing_entries))),
        empty_directories=tuple(empty_directories),
        empty_selections=tuple(sorted(empty_selections, key=lambda item: item.key)),
        missing_selections=tuple(
            sorted(
                missing_selections,
                key=lambda item: (item.archive_root, item.optional, item.expression),
            )
        ),
        type_mismatches=tuple(type_mismatches),
        skipped_link_count=len(skipped_links),
    )

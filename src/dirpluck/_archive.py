"""Archive planning, generated README rendering, and preview rendering."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping

from ._builder_models import ArchivePlan, BuildRequest, EmptySelectionStatus, ResolvedSource
from .config import Config
from .errors import SelectionError
from ._effective import _resolve_execution
from ._selection import select_files


def _markdown_code_span(value: str) -> str:
    """Render one value as an inline Markdown code span."""

    longest = 0
    current = 0
    for char in value:
        if char == "`":
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    fence = "`" * (longest + 1)
    if value.startswith("`") or value.endswith("`"):
        value = f" {value} "
    return f"{fence}{value}{fence}"


def _render_archive_readme(
    request: BuildRequest,
    about_description: str | None,
    sources: tuple[ResolvedSource, ...],
    selection_counts: Mapping[str, int],
    target_overlaps: Mapping[str, tuple[tuple[str, int], ...]],
) -> str:
    lines = ["# Archive contents", ""]
    if about_description is not None:
        lines.extend([about_description, ""])

    for source in sorted(sources, key=lambda item: (item.archive_root, item.key)):
        archive_root = source.archive_root
        if source.source_kind == "directory":
            archive_root = f"{archive_root.rstrip('/')}/"
        lines.extend([f"## {_markdown_code_span(archive_root)}", ""])
        lines.append(f"Files: {selection_counts[source.key]}")
        if request.paths:
            lines.append(f"Source: {_markdown_code_span(source.directory.as_posix())}")
        target_sources = {target.archive_root: target for target in sources if target.kind == "target"}
        for target_root, count in target_overlaps.get(source.key, ()):
            unit = "file" if count == 1 else "files"
            verb = "is" if count == 1 else "are"
            target = target_root
            target_source = target_sources.get(target_root)
            if target_source is None or target_source.source_kind == "directory":
                target = f"{target.rstrip('/')}/"
            lines.append(
                f"Target overlap: {count} selected {unit} {verb} also included under "
                f"{_markdown_code_span(target)}."
            )
        descriptions = tuple(
            description
            for description in (source.scope_description, source.description)
            if description is not None
        )
        if descriptions:
            lines.extend(["", "\n\n".join(descriptions)])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def plan_archive(
    config: Config,
    request: BuildRequest,
    *,
    allow_missing: bool = False,
) -> ArchivePlan:
    """Resolve archive entries without writing an archive."""

    effective, sources = _resolve_execution(config, request)

    archive_entries: dict[str, Path] = {}
    atomic_file_paths: set[str] = set()
    selected_physical_entries: dict[str, set[Path]] = {}
    missing_entries: list[str] = []
    optional_missing_entries: list[str] = []
    empty_selections: list[EmptySelectionStatus] = []
    selection_counts: dict[str, int] = {}
    skipped_links: set[Path] = set()

    for source in sources:
        result = select_files(source, allow_missing=allow_missing)
        skipped_links.update(result.skipped_links)
        selection_counts[source.key] = len(result.files)
        selected_physical_entries[source.key] = {file.resolve() for file in result.files}
        missing_entries.extend(f"{source.archive_root}/{relative}" for relative in result.missing)
        optional_missing_entries.extend(f"{source.archive_root}/{relative}" for relative in result.optional_missing)

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
            if source.source_kind == "file":
                arcname = source.archive_root
            else:
                relative = file.relative_to(source.directory).as_posix()
                arcname = f"{source.archive_root}/{relative}"
            source_resolved = file.resolve()
            previous = archive_entries.get(arcname)
            if previous is not None and previous.resolve() != source_resolved:
                raise SelectionError(f"multiple files resolve to the same archive path {arcname!r}: {previous} and {file}")
            conflict_candidates = archive_entries if source.source_kind == "file" else atomic_file_paths
            for existing in conflict_candidates:
                if existing == arcname:
                    continue
                if existing.startswith(arcname + "/") or arcname.startswith(existing + "/"):
                    raise SelectionError(
                        "archive file/directory path conflict between "
                        f"{existing!r} and {arcname!r}"
                    )
            archive_entries[arcname] = file
            if source.source_kind == "file":
                atomic_file_paths.add(arcname)

    empty_directories = sorted({
        status.archive_root
        for status in empty_selections
        if status.allow_empty and not any(arcname.startswith(f"{status.archive_root}/") for arcname in archive_entries)
    })
    targets = tuple(source for source in sources if source.kind == "target")
    target_overlaps: dict[str, tuple[tuple[str, int], ...]] = {}
    for source in sources:
        if source.kind != "always":
            continue
        overlaps: list[tuple[str, int]] = []
        source_entries = selected_physical_entries[source.key]
        for target in targets:
            count = len(source_entries & selected_physical_entries[target.key])
            if count:
                overlaps.append((target.archive_root, count))
        if overlaps:
            target_overlaps[source.key] = tuple(sorted(overlaps))

    readme = _render_archive_readme(
        request,
        effective.about_description,
        sources,
        selection_counts,
        target_overlaps,
    )
    return ArchivePlan(
        entries=MappingProxyType(dict(sorted(archive_entries.items()))),
        readme=readme,
        missing=tuple(sorted(set(missing_entries))),
        optional_missing=tuple(sorted(set(optional_missing_entries))),
        empty_directories=tuple(empty_directories),
        empty_selections=tuple(sorted(empty_selections, key=lambda item: item.key)),
        skipped_link_count=len(skipped_links),
    )


def render_link_skip_note(count: int, *, preview: bool) -> str:
    """Render one CLI note for link-like entries skipped during archive selection."""

    unit = "entry" if count == 1 else "entries"
    verb = "was" if count == 1 else "were"
    outcome = "will not be archived" if preview else "not archived"
    return (
        f"Note: {count} link-like filesystem {unit} "
        f"(symbolic links or Windows junctions) {verb} skipped and {outcome}."
    )


def render_archive_tree(plan: ArchivePlan | Mapping[str, Path] | tuple[str, ...] | list[str]) -> str:
    """Render archive entry paths as a deterministic tree, marking missing paths."""

    if isinstance(plan, ArchivePlan):
        empty_roots = {status.archive_root for status in plan.empty_selections}
        directory_paths = set(plan.empty_directories) | empty_roots
        paths = ["README.md", *plan.entries.keys(), *plan.missing, *plan.optional_missing, *directory_paths]
        missing = set(plan.missing)
        optional_missing = set(plan.optional_missing)
    else:
        paths = list(plan.keys()) if isinstance(plan, Mapping) else list(plan)
        missing = set()
        optional_missing = set()
        directory_paths = set()

    tree: dict[str, dict] = {}
    for path in sorted(set(paths)):
        node = tree
        for part in PurePosixPath(path).parts:
            node = node.setdefault(part, {})
    if not tree:
        return "(empty)"

    lines: list[str] = []

    def walk(node: dict[str, dict], prefix: str, parts: tuple[str, ...]) -> None:
        items = sorted(node.items())
        for index, (name, children) in enumerate(items):
            last = index == len(items) - 1
            branch = "└── " if last else "├── "
            current_parts = (*parts, name)
            current = PurePosixPath(*current_parts).as_posix()
            if current in missing:
                suffix = " [missing]"
            elif current in optional_missing:
                suffix = " [optional missing]"
            else:
                suffix = "/" if children or current in directory_paths else ""
            lines.append(f"{prefix}{branch}{name}{suffix}")
            if children:
                walk(children, prefix + ("    " if last else "│   "), current_parts)

    walk(tree, "", ())
    if isinstance(plan, ArchivePlan) and plan.empty_selections:
        lines.extend(["", "Empty results:"])
        for status in plan.empty_selections:
            outcome = "allowed" if status.allow_empty else "would error"
            lines.append(f"- {status.label} (`{status.archive_root}/`): empty, {outcome}")
    if isinstance(plan, ArchivePlan) and plan.skipped_link_count:
        lines.extend(["", render_link_skip_note(plan.skipped_link_count, preview=True)])
    return "\n".join(lines)

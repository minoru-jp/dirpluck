"""Archive planning, generated README rendering, and preview rendering."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TypeAlias

from ._archive_models import ArchivePlan
from ._output_models import ArchivePresentation
from ._archive_payload import ArchivePayload
from ._extraction_models import (
    ExtractedSource,
    ExtractionResult,
    SelectionTypeMismatchStatus,
)


_ArchiveTree: TypeAlias = dict[str, "_ArchiveTree"]


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


def _render_source_metadata(
    source: ExtractedSource,
    *,
    heading_level: int,
    presentation: ArchivePresentation,
    include_description: bool = True,
) -> list[str]:
    archive_root = source.archive_root
    if source.source_kind == "directory":
        archive_root = f"{archive_root.rstrip('/')}/"
    lines = [f"{'#' * heading_level} {_markdown_code_span(archive_root)}", ""]
    if include_description and source.description is not None:
        lines.extend([source.description, ""])
    lines.append(f"Files: {source.selected_count}")
    if presentation.show_source_paths:
        lines.append(f"Source: {_markdown_code_span(source.source_path.as_posix())}")
    for overlap in source.target_overlaps:
        unit = "file" if overlap.count == 1 else "files"
        verb = "is" if overlap.count == 1 else "are"
        target = overlap.archive_root
        if overlap.source_kind == "directory":
            target = f"{target.rstrip('/')}/"
        lines.append(
            f"Target overlap: {overlap.count} selected {unit} {verb} also included under "
            + f"{_markdown_code_span(target)}."
        )
    lines.append("")
    return lines


def _scope_heading(name: str | None) -> str:
    if name is None:
        return "### Scope: (unnamed)"
    return f"### Scope: {_markdown_code_span(name)}"


def _render_target_sources(
    presentation: ArchivePresentation,
    sources: tuple[ExtractedSource, ...],
) -> list[str]:
    lines = ["## Targets", ""]
    scopes: dict[str | None, list[ExtractedSource]] = {}
    for source in sources:
        scopes.setdefault(source.scope_name, []).append(source)

    for scope_name, scope_sources in scopes.items():
        lines.extend([_scope_heading(scope_name), ""])
        scope_description = next(
            (
                source.scope_description
                for source in scope_sources
                if source.scope_description is not None
            ),
            None,
        )
        if scope_description is not None:
            lines.extend([scope_description, ""])

        directory_targets = tuple(
            sorted(
                (source for source in scope_sources if source.source_kind == "directory"),
                key=lambda item: (item.archive_root, item.key),
            )
        )
        file_targets = tuple(
            sorted(
                (source for source in scope_sources if source.source_kind == "file"),
                key=lambda item: (item.archive_root, item.key),
            )
        )

        if directory_targets:
            lines.extend(["#### Pluck", ""])
            pluck_description = next(
                (
                    source.description
                    for source in directory_targets
                    if source.description is not None
                ),
                None,
            )
            if pluck_description is not None:
                lines.extend([pluck_description, ""])
            for source in directory_targets:
                lines.extend(
                    _render_source_metadata(
                        source,
                        heading_level=5,
                        presentation=presentation,
                        include_description=False,
                    )
                )

        for source in file_targets:
            lines.extend(
                _render_source_metadata(
                    source,
                    heading_level=4,
                    presentation=presentation,
                    include_description=False,
                )
            )
    return lines


def _conditional_about_description(
    presentation: ArchivePresentation,
    sources: tuple[ExtractedSource, ...],
) -> str | None:
    has_targets = any(source.role == "target" for source in sources)
    has_always = any(source.role == "fixed" for source in sources)
    if not has_targets and not has_always:
        return presentation.description_empty
    if not has_targets:
        return presentation.description_no_targets
    if not has_always:
        return presentation.description_no_always
    return None


def _render_layout_descriptions(
    presentation: ArchivePresentation,
    sources: tuple[ExtractedSource, ...],
) -> list[str]:
    used = sorted(
        {source.layout_name for source in sources if source.layout_name is not None},
        key=str.casefold,
    )
    described = [
        (name, presentation.layout_descriptions.get(name))
        for name in used
        if presentation.layout_descriptions.get(name) is not None
    ]
    if not described:
        return []
    lines = ["## Layouts", ""]
    for name, description in described:
        lines.extend([f"### {_markdown_code_span(f'{name}/')}", ""])
        if description is None:
            raise AssertionError("described Layout unexpectedly has no description")
        lines.extend([description, ""])
    return lines


def _render_archive_readme(
    presentation: ArchivePresentation,
    sources: tuple[ExtractedSource, ...],
) -> str:
    lines = ["# Archive contents", ""]
    if presentation.about_description is not None:
        lines.extend([presentation.about_description, ""])
    conditional_description = _conditional_about_description(presentation, sources)
    if conditional_description is not None:
        lines.extend([conditional_description, ""])

    if not sources:
        lines.extend(["No sources were selected. This Archive contains only `README.md`.", ""])
        return "\n".join(lines).rstrip() + "\n"

    fixed_sources = tuple(
        sorted(
            (source for source in sources if source.role == "fixed"),
            key=lambda item: (item.archive_root, item.key),
        )
    )
    target_sources = tuple(source for source in sources if source.role == "target")

    lines.extend(_render_layout_descriptions(presentation, sources))

    if target_sources:
        scope_note = (
            '`Scope: "..."` identifies only the selection range used to find Targets; '
            + "it does not imply priority, importance, or hierarchy. Any additional meaning "
            + "is stated in that Scope's description."
        )
        lines.extend(
            [
                scope_note,
                "",
            ]
        )

    for source in fixed_sources:
        lines.extend(
            _render_source_metadata(
                source,
                heading_level=2,
                presentation=presentation,
            )
        )

    if target_sources:
        lines.extend(_render_target_sources(presentation, target_sources))

    return "\n".join(lines).rstrip() + "\n"


def _render_type_mismatch(status: SelectionTypeMismatchStatus) -> str:
    expected_directory = status.expected_kind == "directory"
    expected = "directory" if expected_directory else "file"
    actual = "file" if expected_directory else "directory"
    listed = ", ".join(repr(name) for name in status.actual_names)
    role = "optional " if status.optional else ""
    if expected_directory:
        hint = f"remove the trailing '/' from {status.pattern!r} if the {actual} was intended"
    else:
        hint = f"add a trailing '/' to {status.pattern!r} if the {actual} was intended"
    noun = (
        actual
        if len(status.actual_names) == 1
        else ("directories" if actual == "directory" else "files")
    )
    verb = "exists" if len(status.actual_names) == 1 else "exist"
    return (
        f"{status.source_label}: {role}{expected} pattern {status.pattern!r} did not match, "
        + f"but matching {noun} {listed} {verb}; {hint}"
    )


def create_archive_plan(
    extraction: ExtractionResult,
    presentation: ArchivePresentation,
) -> ArchivePlan:
    readme = _render_archive_readme(presentation, extraction.sources)
    return ArchivePlan(
        payload=ArchivePayload(
            entries=extraction.entries,
            readme=readme,
            empty_directories=extraction.empty_directories,
        ),
        missing=extraction.missing,
        optional_missing=extraction.optional_missing,
        empty_selections=extraction.empty_selections,
        missing_selections=extraction.missing_selections,
        diagnostics=tuple(
            sorted({_render_type_mismatch(status) for status in extraction.type_mismatches})
        ),
        skipped_link_count=extraction.skipped_link_count,
    )


def render_link_skip_note(count: int, *, preview: bool) -> str:
    """Render one CLI note for link-like entries skipped during archive selection."""

    unit = "entry" if count == 1 else "entries"
    verb = "was" if count == 1 else "were"
    outcome = "will not be archived" if preview else "not archived"
    return (
        f"Note: {count} link-like filesystem {unit} "
        + f"(symbolic links or Windows junctions) {verb} skipped and {outcome}."
    )


def render_archive_tree(plan: ArchivePlan) -> str:
    """Render one archive plan as a deterministic preview tree."""

    empty_roots = {status.archive_root for status in plan.empty_selections}
    directory_paths = set(plan.empty_directories) | empty_roots
    missing_directory_paths = {path[:-1] for path in plan.missing if path.endswith("/")}
    optional_missing_directory_paths = {
        path[:-1] for path in plan.optional_missing if path.endswith("/")
    }
    missing = {path[:-1] if path.endswith("/") else path for path in plan.missing}
    optional_missing = {path[:-1] if path.endswith("/") else path for path in plan.optional_missing}
    directory_paths |= missing_directory_paths | optional_missing_directory_paths
    paths = [
        "README.md",
        *plan.entries.keys(),
        *missing,
        *optional_missing,
        *directory_paths,
    ]

    tree: _ArchiveTree = {}
    for path in sorted(set(paths)):
        node = tree
        for part in PurePosixPath(path).parts:
            node = node.setdefault(part, {})
    if not tree:
        return "(empty)"

    lines: list[str] = []

    def walk(node: _ArchiveTree, prefix: str, parts: tuple[str, ...]) -> None:
        items = sorted(node.items())
        for index, (name, children) in enumerate(items):
            last = index == len(items) - 1
            branch = "└── " if last else "├── "
            current_parts = (*parts, name)
            current = PurePosixPath(*current_parts).as_posix()
            if current in missing:
                suffix = ("/" if current in directory_paths else "") + " [missing]"
            elif current in optional_missing:
                suffix = ("/" if current in directory_paths else "") + " [optional missing]"
            else:
                suffix = "/" if children or current in directory_paths else ""
            lines.append(f"{prefix}{branch}{name}{suffix}")
            if children:
                walk(children, prefix + ("    " if last else "│   "), current_parts)

    walk(tree, "", ())
    if plan.missing_selections:
        lines.extend(["", "Unmatched selection entries:"])
        for status in plan.missing_selections:
            marker = "optional missing" if status.optional else "missing"
            lines.append(
                f"- {status.source_label} (`{status.archive_root}/`): "
                + f"{status.expression} [{marker}]"
            )
    if plan.empty_selections:
        lines.extend(["", "Empty results:"])
        for status in plan.empty_selections:
            outcome = "allowed" if status.allow_empty else "would error"
            lines.append(f"- {status.label} (`{status.archive_root}/`): empty, {outcome}")
    if plan.skipped_link_count:
        lines.extend(["", render_link_skip_note(plan.skipped_link_count, preview=True)])
    return "\n".join(lines)

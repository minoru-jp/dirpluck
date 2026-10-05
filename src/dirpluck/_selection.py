"""Filesystem selection for resolved builder sources."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from ._filesystem import safe_is_link_like
from ._extraction_models import SelectionTypeMismatchStatus
from ._resolution_models import ResolvedSource
from ._selection_models import ExclusionPattern, IncludePattern, MatchPattern, PathExclusion
from .errors import SelectionError


_EntryKind = Literal["file", "directory", "link", "unsupported"]


@dataclass(frozen=True)
class _IncludeMatchResult:
    entries: tuple[Path, ...]
    skipped_links: tuple[Path, ...]
    unsupported_entries: tuple[Path, ...]
    wrong_type_entries: tuple[Path, ...] = ()


@dataclass(frozen=True)
class _CollectedFiles:
    files: tuple[Path, ...]
    skipped_links: tuple[Path, ...]


@dataclass(frozen=True)
class _SelectionResult:
    files: tuple[Path, ...]
    missing: tuple[str, ...]
    optional_missing: tuple[str, ...]
    skipped_links: tuple[Path, ...] = ()
    opaque_missing: tuple[str, ...] = ()
    opaque_optional_missing: tuple[str, ...] = ()
    type_mismatches: tuple[SelectionTypeMismatchStatus, ...] = ()


def _entry_kind(entry: Path) -> _EntryKind:
    """Classify one filesystem entry without ever following link-like entries."""

    if safe_is_link_like(entry):
        return "link"
    if entry.is_file():
        return "file"
    if entry.is_dir():
        return "directory"
    return "unsupported"


def _directory_prefixes(relative: str, *, include_self: bool) -> tuple[str, ...]:
    parts = PurePosixPath(relative).parts
    limit = len(parts) if include_self else max(len(parts) - 1, 0)
    return tuple("/".join(parts[:index]) + "/" for index in range(1, limit + 1))


def _selection_entry_label(pattern: IncludePattern | MatchPattern) -> str:
    if isinstance(pattern, MatchPattern):
        return f"{{ match = {pattern.raw!r} }}"
    return pattern.raw


def _entry_is_excluded(
    relative: str,
    exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...],
    *,
    kind: _EntryKind,
) -> bool:
    """Apply normalized ignore rules to one classified filesystem entry."""

    path = PurePosixPath(relative)
    if kind == "file":
        regex_candidates = (
            relative,
            *_directory_prefixes(relative, include_self=False),
        )
    elif kind == "directory":
        regex_candidates = _directory_prefixes(relative, include_self=True)
    elif kind == "link":
        regex_candidates = (
            relative,
            relative + "/",
            *_directory_prefixes(relative, include_self=False),
        )
    else:
        # Unsupported special entries use file-like ignore semantics.
        regex_candidates = (
            relative,
            *_directory_prefixes(relative, include_self=False),
        )

    for exclusion in exclusions:
        if isinstance(exclusion, MatchPattern):
            if any(exclusion.matches(candidate) for candidate in regex_candidates):
                return True
            continue
        if isinstance(exclusion, PathExclusion):
            if exclusion.matches(relative, candidate_directory=kind in {"directory", "link"}):
                return True
            continue

        if kind in {"file", "unsupported"}:
            if any(exclusion.matches(name) for name in path.parts[:-1]):
                return True
            if not exclusion.directory and exclusion.matches(path.name):
                return True
            continue
        if any(exclusion.matches(name) for name in path.parts):
            return True
    return False


def _file_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    return _entry_is_excluded(relative, exclusions, kind="file")


def _directory_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    return _entry_is_excluded(relative, exclusions, kind="directory")


def _link_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    return _entry_is_excluded(relative, exclusions, kind="link")


def _unsupported_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    return _entry_is_excluded(relative, exclusions, kind="unsupported")


def _files_under_entry(
    entry: Path,
    *,
    root: Path,
    source_label: str,
    exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...],
) -> _CollectedFiles:
    """Collect regular files below one selected entry without following link-like entries."""

    entry_relative = entry.relative_to(root).as_posix()
    kind = _entry_kind(entry)
    if kind == "link":
        if _link_is_excluded(entry_relative, exclusions):
            return _CollectedFiles((), ())
        return _CollectedFiles((), (entry,))
    if kind == "file":
        if _file_is_excluded(entry_relative, exclusions):
            return _CollectedFiles((), ())
        return _CollectedFiles((entry,), ())
    if kind == "unsupported":
        return _CollectedFiles((), ())

    if entry_relative != "." and _directory_is_excluded(entry_relative, exclusions):
        return _CollectedFiles((), ())

    files: list[Path] = []
    skipped_links: set[Path] = set()

    def walk(directory: Path) -> None:
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise SelectionError(
                f"cannot inspect selected directory for {source_label}: {directory}"
            ) from exc
        for child in children:
            relative = child.relative_to(root).as_posix()
            kind = _entry_kind(child)
            if kind == "link":
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(child)
                continue
            if kind == "directory":
                if _directory_is_excluded(relative, exclusions):
                    continue
                walk(child)
                continue
            if kind == "file" and not _file_is_excluded(relative, exclusions):
                files.append(child)

    walk(entry)
    return _CollectedFiles(
        tuple(files),
        tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
    )


def _matching_include_entries(
    root: Path,
    pattern: IncludePattern,
    exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...],
) -> _IncludeMatchResult:
    """Resolve one must/may pattern with an explicit final entry type."""

    expected_directory = pattern.kind == "directory"
    candidates: tuple[Path, ...] = (root,)
    skipped_links: set[Path] = set()
    unsupported_entries: set[Path] = set()
    wrong_type_entries: set[Path] = set()
    segments = pattern.segments
    for index, segment in enumerate(segments):
        last = index == len(segments) - 1
        next_candidates: list[Path] = []
        for parent in candidates:
            parent_kind = _entry_kind(parent)
            if parent_kind == "link":
                relative = parent.relative_to(root).as_posix()
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(parent)
                continue
            if parent_kind != "directory":
                continue
            try:
                children = tuple(parent.iterdir())
            except OSError as exc:
                raise SelectionError(
                    f"cannot inspect directory while matching include {pattern.raw!r}: {parent}"
                ) from exc
            next_candidates.extend(child for child in children if segment.matches(child.name))
        checked: list[Path] = []
        for candidate in next_candidates:
            relative = candidate.relative_to(root).as_posix()
            kind = _entry_kind(candidate)
            if kind == "link":
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(candidate)
                continue
            if not last:
                if kind == "directory" and not _directory_is_excluded(relative, exclusions):
                    checked.append(candidate)
                continue

            if expected_directory:
                if kind == "directory":
                    if not _directory_is_excluded(relative, exclusions):
                        checked.append(candidate)
                elif kind == "file":
                    if not _file_is_excluded(relative, exclusions):
                        wrong_type_entries.add(candidate)
                elif not _unsupported_is_excluded(relative, exclusions):
                    unsupported_entries.add(candidate)
                continue

            if kind == "file":
                if not _file_is_excluded(relative, exclusions):
                    checked.append(candidate)
            elif kind == "directory":
                if not _directory_is_excluded(relative, exclusions):
                    wrong_type_entries.add(candidate)
            elif not _unsupported_is_excluded(relative, exclusions):
                unsupported_entries.add(candidate)
        candidates = tuple(checked)
        if not candidates:
            break
    return _IncludeMatchResult(
        tuple(sorted(candidates, key=lambda path: path.as_posix())),
        tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
        tuple(sorted(unsupported_entries, key=lambda path: path.as_posix())),
        tuple(sorted(wrong_type_entries, key=lambda path: path.as_posix())),
    )


def _matching_regex_entries(
    root: Path,
    pattern: MatchPattern,
    exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...],
) -> _IncludeMatchResult:
    """Resolve one full-path match expression below the Selection root."""

    entries: list[Path] = []
    skipped_links: set[Path] = set()
    unsupported_entries: set[Path] = set()

    def walk(directory: Path) -> None:
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise SelectionError(
                f"cannot inspect directory while matching {pattern.raw!r}: {directory}"
            ) from exc

        for child in children:
            relative = child.relative_to(root).as_posix()
            kind = _entry_kind(child)
            if kind == "link":
                if not _link_is_excluded(relative, exclusions):
                    if pattern.matches(relative) or pattern.matches(relative + "/"):
                        skipped_links.add(child)
                continue

            if kind == "directory":
                if _directory_is_excluded(relative, exclusions):
                    continue
                match_path = relative + "/"
                if pattern.matches(match_path):
                    entries.append(child)
                    # Selecting a directory already selects its eligible subtree, so
                    # deeper matches cannot change the final Selection.
                    continue
                walk(child)
                continue

            if kind == "file":
                if not _file_is_excluded(relative, exclusions) and pattern.matches(relative):
                    entries.append(child)
                continue

            if not _unsupported_is_excluded(relative, exclusions) and pattern.matches(relative):
                unsupported_entries.add(child)

    walk(root)
    return _IncludeMatchResult(
        tuple(sorted(entries, key=lambda path: path.as_posix())),
        tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
        tuple(sorted(unsupported_entries, key=lambda path: path.as_posix())),
        (),
    )


def _wrong_type_status(
    source_label: str,
    pattern: IncludePattern,
    entries: tuple[Path, ...],
    *,
    optional: bool,
) -> SelectionTypeMismatchStatus:
    return SelectionTypeMismatchStatus(
        source_label=source_label,
        pattern=pattern.raw,
        expected_kind=pattern.kind,
        actual_names=tuple(entry.name + ("/" if entry.is_dir() else "") for entry in entries),
        optional=optional,
    )


def _wrong_type_error_detail(status: SelectionTypeMismatchStatus) -> str:
    expected_directory = status.expected_kind == "directory"
    expected = "directory" if expected_directory else "file"
    actual = "file" if expected_directory else "directory"
    listed = ", ".join(repr(name) for name in status.actual_names)
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
        f"{expected} pattern {status.pattern!r} did not match, "
        + f"but matching {noun} {listed} {verb}; {hint}"
    )


def select_files(source: ResolvedSource, *, allow_missing: bool = False) -> _SelectionResult:
    """Select files for one resolved source."""

    if source.source_kind == "file":
        return _SelectionResult(files=(source.directory,), missing=(), optional_missing=())

    if source.selection is None:
        raise AssertionError(f"directory source has no Selection: {source.label}")

    selected: dict[str, Path] = {}
    missing: list[str] = []
    link_only_missing: list[str] = []
    unsupported_only_missing: list[str] = []
    mixed_nonselectable_missing: list[str] = []
    optional_missing: list[str] = []
    opaque_missing: list[str] = []
    opaque_optional_missing: list[str] = []
    type_mismatches: list[SelectionTypeMismatchStatus] = []
    wrong_type_required: dict[str, tuple[IncludePattern, tuple[Path, ...]]] = {}
    skipped_links: set[Path] = set()
    root = source.directory
    selection = source.selection

    def collect_pattern(pattern: IncludePattern | MatchPattern, *, optional: bool) -> None:
        if isinstance(pattern, MatchPattern):
            matched = _matching_regex_entries(root, pattern, selection.ignore)
        else:
            matched = _matching_include_entries(root, pattern, selection.ignore)
        skipped_links.update(matched.skipped_links)
        display = _selection_entry_label(pattern)
        if not matched.entries:
            (optional_missing if optional else missing).append(display)
            if isinstance(pattern, MatchPattern):
                (opaque_optional_missing if optional else opaque_missing).append(display)
            elif matched.wrong_type_entries:
                mismatch = _wrong_type_status(
                    source.label,
                    pattern,
                    matched.wrong_type_entries,
                    optional=optional,
                )
                if optional or allow_missing:
                    type_mismatches.append(mismatch)
                if not optional:
                    wrong_type_required[display] = (pattern, matched.wrong_type_entries)
            if not optional:
                if matched.skipped_links and matched.unsupported_entries:
                    mixed_nonselectable_missing.append(display)
                elif matched.skipped_links:
                    link_only_missing.append(display)
                elif matched.unsupported_entries:
                    unsupported_only_missing.append(display)
            return
        for entry in matched.entries:
            collected = _files_under_entry(
                entry,
                root=root,
                source_label=source.label,
                exclusions=selection.ignore,
            )
            skipped_links.update(collected.skipped_links)
            for candidate in collected.files:
                relative = candidate.relative_to(root).as_posix()
                selected[relative] = candidate

    for pattern in selection.must:
        collect_pattern(pattern, optional=False)
    for pattern in selection.may:
        collect_pattern(pattern, optional=True)

    if missing and not allow_missing:
        explained = (
            set(link_only_missing)
            | set(unsupported_only_missing)
            | set(mixed_nonselectable_missing)
            | set(wrong_type_required)
        )
        ordinary = [pattern for pattern in missing if pattern not in explained]
        details: list[str] = []
        if link_only_missing:
            listed = ", ".join(repr(path) for path in link_only_missing)
            details.append(
                "must pattern(s) matched only symbolic links or Windows junctions, "
                + f"which are not selectable: {listed}"
            )
        if unsupported_only_missing:
            listed = ", ".join(repr(path) for path in unsupported_only_missing)
            details.append(
                "must pattern(s) matched only unsupported special filesystem entries, "
                + f"which are not selectable: {listed}"
            )
        if mixed_nonselectable_missing:
            listed = ", ".join(repr(path) for path in mixed_nonselectable_missing)
            details.append(
                "must pattern(s) matched only non-selectable filesystem entries "
                + "(symbolic links, Windows junctions, or unsupported special entries): "
                + f"{listed}"
            )
        for pattern, entries in wrong_type_required.values():
            details.append(
                _wrong_type_error_detail(
                    _wrong_type_status(
                        source.label,
                        pattern,
                        entries,
                        optional=False,
                    )
                )
            )
        if ordinary:
            listed = ", ".join(repr(path) for path in ordinary)
            details.append(f"must pattern(s) with no matches: {listed}")
        raise SelectionError(f"{source.label}: " + "; ".join(details))
    return _SelectionResult(
        files=tuple(selected[key] for key in sorted(selected)),
        missing=tuple(sorted(set(missing))),
        optional_missing=tuple(sorted(set(optional_missing))),
        skipped_links=tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
        opaque_missing=tuple(sorted(set(opaque_missing))),
        opaque_optional_missing=tuple(sorted(set(opaque_optional_missing))),
        type_mismatches=tuple(type_mismatches),
    )


def collect_files(source: ResolvedSource) -> tuple[Path, ...]:
    return select_files(source).files

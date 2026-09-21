"""Filesystem selection for resolved builder sources."""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from ._builder_common import _is_link_like
from ._builder_models import ResolvedSource, SelectionResult, _CollectedFiles, _IncludeMatchResult
from ._config_models import ExclusionPattern, PathExclusion
from .errors import SelectionError


def _name_matches(name: str, pattern: ExclusionPattern) -> bool:
    if pattern.match == "exact":
        return name == pattern.value
    if pattern.match == "prefix":
        return name.startswith(pattern.value)
    if pattern.match == "suffix":
        return name.endswith(pattern.value)
    if pattern.match == "contains":
        return pattern.value in name
    raise AssertionError(f"unknown ignore match kind: {pattern.match}")


def _path_exclusion_matches(relative: str, exclusion: PathExclusion) -> bool:
    if exclusion.directory:
        return relative == exclusion.path or relative.startswith(exclusion.path + "/")
    return relative == exclusion.path


def _file_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion, ...]
) -> bool:
    path = PurePosixPath(relative)
    directory_names = path.parts[:-1]
    for exclusion in exclusions:
        if isinstance(exclusion, PathExclusion):
            if _path_exclusion_matches(relative, exclusion):
                return True
            continue
        if exclusion.directory:
            if any(_name_matches(name, exclusion) for name in directory_names):
                return True
        elif _name_matches(path.name, exclusion):
            return True
    return False

def _directory_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion, ...]
) -> bool:
    path = PurePosixPath(relative)
    for exclusion in exclusions:
        if isinstance(exclusion, PathExclusion):
            if exclusion.directory and _path_exclusion_matches(relative, exclusion):
                return True
            continue
        if exclusion.directory and any(_name_matches(name, exclusion) for name in path.parts):
            return True
    return False

def _link_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion, ...]
) -> bool:
    """Apply ignore semantics to a link-like entry without following its target."""

    path = PurePosixPath(relative)
    for exclusion in exclusions:
        if isinstance(exclusion, PathExclusion):
            if _path_exclusion_matches(relative, exclusion):
                return True
            continue
        if exclusion.directory and any(_name_matches(name, exclusion) for name in path.parts):
            return True
        if not exclusion.directory and _name_matches(path.name, exclusion):
            return True
    return False

def _files_under_entry(
    entry: Path,
    *,
    root: Path,
    source_label: str,
    exclusions: tuple[ExclusionPattern | PathExclusion, ...],
) -> _CollectedFiles:
    """Collect regular files below one selected entry without following link-like entries."""

    entry_relative = entry.relative_to(root).as_posix()
    if _is_link_like(entry):
        if _link_is_excluded(entry_relative, exclusions):
            return _CollectedFiles((), ())
        return _CollectedFiles((), (entry,))
    if entry.is_file():
        if _file_is_excluded(entry_relative, exclusions):
            return _CollectedFiles((), ())
        return _CollectedFiles((entry,), ())
    if not entry.is_dir():
        return _CollectedFiles((), ())

    if entry_relative != "." and _directory_is_excluded(entry_relative, exclusions):
        return _CollectedFiles((), ())

    files: list[Path] = []
    skipped_links: set[Path] = set()

    def walk(directory: Path) -> None:
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise SelectionError(f"cannot inspect selected directory for {source_label}: {directory}") from exc
        for child in children:
            relative = child.relative_to(root).as_posix()
            if _is_link_like(child):
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(child)
                continue
            if child.is_dir():
                if _directory_is_excluded(relative, exclusions):
                    continue
                walk(child)
            elif child.is_file():
                if _file_is_excluded(relative, exclusions):
                    continue
                files.append(child)

    walk(entry)
    return _CollectedFiles(
        tuple(files),
        tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
    )


def _include_name_matches(name: str, pattern: str) -> bool:
    if "*" not in pattern:
        return name == pattern
    prefix, suffix = pattern.split("*", 1)
    return name.startswith(prefix) and name.endswith(suffix) and len(name) >= len(prefix) + len(suffix)


def _matching_include_entries(
    root: Path,
    pattern: str,
    exclusions: tuple[ExclusionPattern | PathExclusion, ...],
) -> _IncludeMatchResult:
    """Resolve one must/may pattern without recursive wildcards or following link-like entries."""

    candidates: tuple[Path, ...] = (root,)
    skipped_links: set[Path] = set()
    unsupported_entries: set[Path] = set()
    parts = PurePosixPath(pattern).parts
    for index, part in enumerate(parts):
        last = index == len(parts) - 1
        next_candidates: list[Path] = []
        for parent in candidates:
            if _is_link_like(parent):
                relative = parent.relative_to(root).as_posix()
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(parent)
                continue
            if not parent.is_dir():
                continue
            try:
                children = tuple(parent.iterdir())
            except OSError as exc:
                raise SelectionError(f"cannot inspect directory while matching include {pattern!r}: {parent}") from exc
            if "*" not in part:
                next_candidates.extend(child for child in children if child.name == part)
            else:
                next_candidates.extend(child for child in children if _include_name_matches(child.name, part))
        checked: list[Path] = []
        for candidate in next_candidates:
            relative = candidate.relative_to(root).as_posix()
            if _is_link_like(candidate):
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(candidate)
                continue
            if candidate.is_dir():
                if _directory_is_excluded(relative, exclusions):
                    continue
                checked.append(candidate)
            elif last and candidate.is_file():
                if _file_is_excluded(relative, exclusions):
                    continue
                checked.append(candidate)
            elif last and not _file_is_excluded(relative, exclusions):
                unsupported_entries.add(candidate)
        candidates = tuple(checked)
        if not candidates:
            break
    return _IncludeMatchResult(
        tuple(sorted(candidates, key=lambda path: path.as_posix())),
        tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
        tuple(sorted(unsupported_entries, key=lambda path: path.as_posix())),
    )


def select_files(source: ResolvedSource, *, allow_missing: bool = False) -> SelectionResult:
    """Select files using required must and optional may patterns plus name ignores."""

    selected: dict[str, Path] = {}
    missing: list[str] = []
    link_only_missing: list[str] = []
    unsupported_only_missing: list[str] = []
    mixed_nonselectable_missing: list[str] = []
    optional_missing: list[str] = []
    skipped_links: set[Path] = set()
    root = source.directory
    selection = source.selection

    def collect_pattern(pattern: str, *, optional: bool) -> None:
        matched = _matching_include_entries(root, pattern, selection.ignore)
        skipped_links.update(matched.skipped_links)
        if not matched.entries:
            (optional_missing if optional else missing).append(pattern)
            if not optional:
                if matched.skipped_links and matched.unsupported_entries:
                    mixed_nonselectable_missing.append(pattern)
                elif matched.skipped_links:
                    link_only_missing.append(pattern)
                elif matched.unsupported_entries:
                    unsupported_only_missing.append(pattern)
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
        explained = set(link_only_missing) | set(unsupported_only_missing) | set(mixed_nonselectable_missing)
        ordinary = [pattern for pattern in missing if pattern not in explained]
        details: list[str] = []
        if link_only_missing:
            listed = ", ".join(repr(path) for path in link_only_missing)
            details.append(
                "must pattern(s) matched only symbolic links or Windows junctions, "
                f"which are not selectable: {listed}"
            )
        if unsupported_only_missing:
            listed = ", ".join(repr(path) for path in unsupported_only_missing)
            details.append(
                "must pattern(s) matched only unsupported special filesystem entries, "
                f"which are not selectable: {listed}"
            )
        if mixed_nonselectable_missing:
            listed = ", ".join(repr(path) for path in mixed_nonselectable_missing)
            details.append(
                "must pattern(s) matched only non-selectable filesystem entries "
                "(symbolic links, Windows junctions, or unsupported special entries): "
                f"{listed}"
            )
        if ordinary:
            listed = ", ".join(repr(path) for path in ordinary)
            details.append(f"must pattern(s) with no matches: {listed}")
        raise SelectionError(f"{source.label} has " + "; ".join(details))
    return SelectionResult(
        files=tuple(selected[key] for key in sorted(selected)),
        missing=tuple(sorted(set(missing))),
        optional_missing=tuple(sorted(set(optional_missing))),
        skipped_links=tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
    )


def collect_files(source: ResolvedSource) -> tuple[Path, ...]:
    return select_files(source).files

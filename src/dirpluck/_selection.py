"""Filesystem selection for resolved builder sources."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path, PurePosixPath
import re

from ._builder_common import _is_link_like
from ._builder_models import ResolvedSource, SelectionResult, _CollectedFiles, _IncludeMatchResult
from ._config_models import ExclusionPattern, MatchPattern, PathExclusion
from .errors import SelectionError


@lru_cache(maxsize=256)
def _compiled_match_pattern(raw: str) -> re.Pattern[str]:
    """Compile one Configuration-validated Selection match expression."""

    return re.compile(raw)


def _directory_prefixes(relative: str, *, include_self: bool) -> tuple[str, ...]:
    parts = PurePosixPath(relative).parts
    limit = len(parts) if include_self else max(len(parts) - 1, 0)
    return tuple("/".join(parts[:index]) + "/" for index in range(1, limit + 1))


def _match_pattern_matches(pattern: MatchPattern, relative: str) -> bool:
    return _compiled_match_pattern(pattern.raw).fullmatch(relative) is not None


def _selection_entry_label(pattern: str | MatchPattern) -> str:
    if isinstance(pattern, MatchPattern):
        return f"{{ match = {pattern.raw!r} }}"
    return pattern


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


def _path_exclusion_matches(
    relative: str,
    exclusion: PathExclusion,
    *,
    candidate_directory: bool,
) -> bool:
    # A trailing '/' narrows a concrete ignore to directories. Without it, the
    # ignore is broad: an entry at that path is excluded whether it is a file
    # or a directory. Descendants are necessarily beneath a directory and are
    # therefore excluded for either spelling.
    if relative.startswith(exclusion.path + "/"):
        return True
    if relative != exclusion.path:
        return False
    return candidate_directory or not exclusion.directory


def _file_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    path = PurePosixPath(relative)
    directory_names = path.parts[:-1]
    for exclusion in exclusions:
        if isinstance(exclusion, MatchPattern):
            if _match_pattern_matches(exclusion, relative):
                return True
            if any(
                _match_pattern_matches(exclusion, directory_path)
                for directory_path in _directory_prefixes(relative, include_self=False)
            ):
                return True
            continue
        if isinstance(exclusion, PathExclusion):
            if _path_exclusion_matches(relative, exclusion, candidate_directory=False):
                return True
            continue
        # A trailing '/' is directory-only. Without it, ignore is broad and
        # applies to both matching file names and matching directory ancestors.
        if any(_name_matches(name, exclusion) for name in directory_names):
            return True
        if not exclusion.directory and _name_matches(path.name, exclusion):
            return True
    return False


def _directory_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    path = PurePosixPath(relative)
    for exclusion in exclusions:
        if isinstance(exclusion, MatchPattern):
            if any(
                _match_pattern_matches(exclusion, directory_path)
                for directory_path in _directory_prefixes(relative, include_self=True)
            ):
                return True
            continue
        if isinstance(exclusion, PathExclusion):
            if _path_exclusion_matches(relative, exclusion, candidate_directory=True):
                return True
            continue
        if any(_name_matches(name, exclusion) for name in path.parts):
            return True
    return False


def _link_is_excluded(
    relative: str, exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...]
) -> bool:
    """Apply ignore semantics to a link-like entry without following its target."""

    path = PurePosixPath(relative)
    for exclusion in exclusions:
        if isinstance(exclusion, MatchPattern):
            if _match_pattern_matches(exclusion, relative) or _match_pattern_matches(
                exclusion, relative + "/"
            ):
                return True
            if any(
                _match_pattern_matches(exclusion, directory_path)
                for directory_path in _directory_prefixes(relative, include_self=False)
            ):
                return True
            continue
        if isinstance(exclusion, PathExclusion):
            # Link-like entries are never followed, so either broad or
            # directory-only spelling may suppress their diagnostic at the
            # exact path, matching the existing conservative link behavior.
            if relative == exclusion.path or relative.startswith(exclusion.path + "/"):
                return True
            continue
        if any(_name_matches(name, exclusion) for name in path.parts):
            return True
    return False


def _files_under_entry(
    entry: Path,
    *,
    root: Path,
    source_label: str,
    exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...],
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
            raise SelectionError(
                f"cannot inspect selected directory for {source_label}: {directory}"
            ) from exc
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
    return (
        name.startswith(prefix) and name.endswith(suffix) and len(name) >= len(prefix) + len(suffix)
    )


def _matching_include_entries(
    root: Path,
    pattern: str,
    exclusions: tuple[ExclusionPattern | PathExclusion | MatchPattern, ...],
) -> _IncludeMatchResult:
    """Resolve one must/may pattern with an explicit final entry type."""

    expected_directory = pattern.endswith("/")
    body = pattern[:-1] if expected_directory else pattern
    candidates: tuple[Path, ...] = (root,)
    skipped_links: set[Path] = set()
    unsupported_entries: set[Path] = set()
    wrong_type_entries: set[Path] = set()
    parts = PurePosixPath(body).parts
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
                raise SelectionError(
                    f"cannot inspect directory while matching include {pattern!r}: {parent}"
                ) from exc
            if "*" not in part:
                next_candidates.extend(child for child in children if child.name == part)
            else:
                next_candidates.extend(
                    child for child in children if _include_name_matches(child.name, part)
                )
        checked: list[Path] = []
        for candidate in next_candidates:
            relative = candidate.relative_to(root).as_posix()
            if _is_link_like(candidate):
                if not _link_is_excluded(relative, exclusions):
                    skipped_links.add(candidate)
                continue
            if not last:
                if candidate.is_dir():
                    if _directory_is_excluded(relative, exclusions):
                        continue
                    checked.append(candidate)
                continue

            if expected_directory:
                if candidate.is_dir():
                    if _directory_is_excluded(relative, exclusions):
                        continue
                    checked.append(candidate)
                elif candidate.is_file():
                    if not _file_is_excluded(relative, exclusions):
                        wrong_type_entries.add(candidate)
                elif not _file_is_excluded(relative, exclusions):
                    unsupported_entries.add(candidate)
                continue

            if candidate.is_file():
                if _file_is_excluded(relative, exclusions):
                    continue
                checked.append(candidate)
            elif candidate.is_dir():
                if not _directory_is_excluded(relative, exclusions):
                    wrong_type_entries.add(candidate)
            elif not _file_is_excluded(relative, exclusions):
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

    compiled = _compiled_match_pattern(pattern.raw)
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
            if _is_link_like(child):
                if not _link_is_excluded(relative, exclusions):
                    if (
                        compiled.fullmatch(relative) is not None
                        or compiled.fullmatch(relative + "/") is not None
                    ):
                        skipped_links.add(child)
                continue

            if child.is_dir():
                if _directory_is_excluded(relative, exclusions):
                    continue
                match_path = relative + "/"
                if compiled.fullmatch(match_path) is not None:
                    entries.append(child)
                    # Selecting a directory already selects its eligible subtree, so
                    # deeper matches cannot change the final Selection.
                    continue
                walk(child)
                continue

            if child.is_file():
                if _file_is_excluded(relative, exclusions):
                    continue
                if compiled.fullmatch(relative) is not None:
                    entries.append(child)
                continue

            if (
                not _file_is_excluded(relative, exclusions)
                and compiled.fullmatch(relative) is not None
            ):
                unsupported_entries.add(child)

    walk(root)
    return _IncludeMatchResult(
        tuple(sorted(entries, key=lambda path: path.as_posix())),
        tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
        tuple(sorted(unsupported_entries, key=lambda path: path.as_posix())),
        (),
    )


def _wrong_type_diagnostic(
    source_label: str,
    pattern: str,
    entries: tuple[Path, ...],
    *,
    optional: bool,
) -> str:
    expected_directory = pattern.endswith("/")
    expected = "directory" if expected_directory else "file"
    actual = "file" if expected_directory else "directory"
    rendered: list[str] = []
    for entry in entries:
        name = entry.name + ("/" if entry.is_dir() else "")
        rendered.append(repr(name))
    listed = ", ".join(rendered)
    role = "optional " if optional else ""
    if expected_directory:
        hint = f"remove the trailing '/' from {pattern!r} if the {actual} was intended"
    else:
        hint = f"add a trailing '/' to {pattern!r} if the {actual} was intended"
    noun = actual if len(entries) == 1 else ("directories" if actual == "directory" else "files")
    verb = "exists" if len(entries) == 1 else "exist"
    return (
        f"{source_label}: {role}{expected} pattern {pattern!r} did not match, "
        + f"but matching {noun} {listed} {verb}; {hint}"
    )


def select_files(source: ResolvedSource, *, allow_missing: bool = False) -> SelectionResult:
    """Select files for one resolved source."""

    if source.source_kind == "file":
        return SelectionResult(files=(source.directory,), missing=(), optional_missing=())

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
    diagnostics: list[str] = []
    wrong_type_required: dict[str, tuple[Path, ...]] = {}
    skipped_links: set[Path] = set()
    root = source.directory
    selection = source.selection

    def collect_pattern(pattern: str | MatchPattern, *, optional: bool) -> None:
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
                diagnostic = _wrong_type_diagnostic(
                    source.label,
                    pattern,
                    matched.wrong_type_entries,
                    optional=optional,
                )
                if optional or allow_missing:
                    diagnostics.append(diagnostic)
                if not optional:
                    wrong_type_required[display] = matched.wrong_type_entries
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
        for display, entries in wrong_type_required.items():
            details.append(
                _wrong_type_diagnostic(
                    source.label,
                    display,
                    entries,
                    optional=False,
                ).removeprefix(f"{source.label}: ")
            )
        if ordinary:
            listed = ", ".join(repr(path) for path in ordinary)
            details.append(f"must pattern(s) with no matches: {listed}")
        raise SelectionError(f"{source.label}: " + "; ".join(details))
    return SelectionResult(
        files=tuple(selected[key] for key in sorted(selected)),
        missing=tuple(sorted(set(missing))),
        optional_missing=tuple(sorted(set(optional_missing))),
        skipped_links=tuple(sorted(skipped_links, key=lambda path: path.as_posix())),
        opaque_missing=tuple(sorted(set(opaque_missing))),
        opaque_optional_missing=tuple(sorted(set(opaque_optional_missing))),
        diagnostics=tuple(sorted(set(diagnostics))),
    )


def collect_files(source: ResolvedSource) -> tuple[Path, ...]:
    return select_files(source).files

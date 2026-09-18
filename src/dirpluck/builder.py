"""Directory resolution, file selection, archive planning, and ZIP creation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Mapping
import os
import tempfile
import zipfile

from .config import (
    Companion,
    Config,
    ConfigurationImport,
    ExclusionPattern,
    Selection,
    SharedPatterns,
    _materialize_selection,
    _merge_root_visible_shared,
    load_config,
)
from .errors import ConfigurationError, SelectionError


@dataclass(frozen=True)
class BuildRequest:
    """One build request with zero or more runtime Targets, one Case, and output sequence."""

    directories: tuple[Path, ...] = ()
    case: str | None = None
    sequence: int | None = None

    @classmethod
    def create(
        cls,
        *directories: str | Path,
        case: str | None = None,
        sequence: int | None = None,
    ) -> "BuildRequest":
        return cls(
            directories=tuple(Path(directory) for directory in directories),
            case=case,
            sequence=sequence,
        )


@dataclass(frozen=True)
class ResolvedSource:
    """A configured target or companion resolved to a concrete directory."""

    key: str
    kind: str
    name: str | None
    description: str
    directory: Path
    archive_root: str
    selection: Selection
    source: str
    config_location: str
    import_name: str | None

    @property
    def label(self) -> str:
        if self.kind == "target":
            return "target" if self.name is None else f"target {self.name!r}"
        return f"companion {self.name!r}"


@dataclass(frozen=True)
class SelectionResult:
    """Files selected for one source plus required and optional unmatched patterns."""

    files: tuple[Path, ...]
    missing: tuple[str, ...]
    optional_missing: tuple[str, ...]


@dataclass(frozen=True)
class EmptySelectionStatus:
    """One target or companion that selected no files during archive planning."""

    key: str
    label: str
    archive_root: str
    if_empty: str


@dataclass(frozen=True)
class ArchivePlan:
    """Exact archive entries, generated README, and preview-only status details."""

    entries: Mapping[str, Path]
    readme: str
    missing: tuple[str, ...] = ()
    optional_missing: tuple[str, ...] = ()
    empty_directories: tuple[str, ...] = ()
    empty_selections: tuple[EmptySelectionStatus, ...] = ()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_directory(
    path: str | Path,
    cwd: Path,
    *,
    label: str,
    allow_cwd: bool,
) -> tuple[Path, str]:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{label} does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise SelectionError(f"{label} is not a directory: {candidate}")
    try:
        relative = resolved.relative_to(cwd)
    except ValueError as exc:
        raise SelectionError(
            f"{label} must be within the Configuration execution root: {resolved}"
        ) from exc

    if relative == Path("."):
        if not allow_cwd:
            raise SelectionError(
                f"{label} must name a directory below the Configuration execution root"
            )
        archive_root = resolved.name
        if not archive_root:
            raise SelectionError(
                f"{label} cannot use the filesystem root as the target directory"
            )
        return resolved, archive_root
    return resolved, relative.as_posix()


def _available_cases(config: Config) -> tuple[str, ...]:
    if config.target is not None:
        return tuple(sorted(config.target.cases))
    return tuple(sorted({
        case
        for companion in config.companions.values()
        for case in companion.cases
    }))


def _validate_request(config: Config, request: BuildRequest) -> None:
    if request.sequence is not None:
        if isinstance(request.sequence, bool) or not isinstance(request.sequence, int) or request.sequence < 1:
            raise SelectionError("output sequence must be an integer greater than or equal to 1")
        if not config.output.generated:
            raise SelectionError("output sequence can only be used with generated output")

    if config.target is None:
        if request.directories:
            raise SelectionError(
                "the configuration does not define [target]; DIRECTORY must not be specified"
            )
    elif not request.directories:
        raise SelectionError(
            "the configuration defines [target]; DIRECTORY is required (one or more may be specified)"
        )

    if request.case is None:
        return

    available = _available_cases(config)
    if request.case not in available:
        listed = ", ".join(available) or "(none)"
        raise SelectionError(
            f"case {request.case!r} is not defined; available cases: {listed}"
        )


def _selected_target(
    config: Config,
    case: str | None,
    *,
    shared: SharedPatterns,
) -> tuple[Selection, str] | None:
    target = config.target
    if target is None:
        return None

    if case is None:
        if target.default is None:
            available = ", ".join(sorted(target.cases)) or "(none)"
            raise SelectionError(
                "the configuration has no default [target]; "
                f"specify --case NAME (available: {available})"
            )
        return _materialize_selection(target.default, shared, "[target]"), "[target]"

    try:
        selection = target.cases[case]
    except KeyError as exc:
        available = ", ".join(sorted(target.cases)) or "(none)"
        raise SelectionError(
            f"case {case!r} is not defined for target; available cases: {available}"
        ) from exc
    location = f"[target.case.{case}]"
    return _materialize_selection(selection, shared, location), location


def _selected_companion(
    companion: Companion,
    case: str | None,
    *,
    shared: SharedPatterns,
    config_location_prefix: str = "companion",
) -> tuple[Selection, str]:
    if case is not None and case in companion.cases:
        location = f"[{config_location_prefix}.{companion.name}.case.{case}]"
        return _materialize_selection(companion.cases[case], shared, location), location
    location = f"[{config_location_prefix}.{companion.name}]"
    return _materialize_selection(companion.selection, shared, location), location


def _available_companion_cases(
    companions: Mapping[str, Companion],
) -> tuple[str, ...]:
    return tuple(sorted({
        case
        for companion in companions.values()
        for case in companion.cases
    }))


def _validate_import_companion_case(
    imported: Mapping[str, Companion],
    added: Mapping[str, Companion],
    case: str | None,
) -> None:
    if case is None:
        return
    available = tuple(sorted(set(_available_companion_cases(imported)) | set(_available_companion_cases(added))))
    if case not in available:
        listed = ", ".join(available) or "(none)"
        raise SelectionError(
            f"case {case!r} is not defined for any companion in the import namespace; "
            f"available companion cases: {listed}"
        )


def _resolve_companion_sources(
    companions: Mapping[str, Companion],
    case: str | None,
    *,
    execution_root: Path,
    shared: SharedPatterns,
    key_prefix: str = "",
    import_name: str | None = None,
    config_location_prefix: str = "companion",
    allow_execution_root: bool = False,
) -> tuple[ResolvedSource, ...]:
    resolved_sources: list[ResolvedSource] = []
    for name, companion in companions.items():
        selection, config_location = _selected_companion(
            companion,
            case,
            shared=shared,
            config_location_prefix=config_location_prefix,
        )
        logical_name = name if import_name is None else f"{import_name}.{name}"
        directory, archive_root = _resolve_directory(
            companion.path,
            execution_root,
            label=f"companion {logical_name!r}",
            allow_cwd=allow_execution_root,
        )
        resolved_sources.append(
            ResolvedSource(
                key=f"{key_prefix}companion:{name}",
                kind="companion",
                name=logical_name,
                description=selection.description,
                directory=directory,
                archive_root=archive_root,
                selection=selection,
                source=f"fixed path `{companion.path}`",
                config_location=config_location,
                import_name=import_name,
            )
        )
    return tuple(resolved_sources)


def _resolve_configuration_sources(
    config: Config,
    request: BuildRequest,
    *,
    execution_root: Path,
    shared: SharedPatterns,
    key_prefix: str = "",
    import_name: str | None = None,
) -> tuple[ResolvedSource, ...]:
    """Resolve Target and Companion sources for one Configuration execution root."""

    _validate_request(config, request)
    resolved_sources: list[ResolvedSource] = []

    selected_target = _selected_target(config, request.case, shared=shared)
    if selected_target is not None:
        target_selection, target_location = selected_target
        target_count = len(request.directories)
        seen_target_directories: set[Path] = set()
        for index, requested_directory in enumerate(request.directories, start=1):
            target_directory, target_archive_root = _resolve_directory(
                requested_directory,
                execution_root,
                label=f"target {index}" if target_count > 1 else "target",
                allow_cwd=True,
            )
            if target_directory in seen_target_directories:
                raise SelectionError(
                    f"target directories must resolve to distinct directories: {target_directory}"
                )
            seen_target_directories.add(target_directory)
            local_key = "target" if target_count == 1 else f"target:{index}"
            if import_name is None:
                source_text = f"CLI input #{index}" if target_count > 1 else "CLI input"
                source_name = None if target_count == 1 else target_archive_root
            else:
                source_text = (
                    f"import `{import_name}` target #{index}"
                    if target_count > 1
                    else f"import `{import_name}` target"
                )
                source_name = None if target_count == 1 else target_archive_root
            resolved_sources.append(
                ResolvedSource(
                    key=f"{key_prefix}{local_key}",
                    kind="target",
                    name=source_name,
                    description=target_selection.description,
                    directory=target_directory,
                    archive_root=target_archive_root,
                    selection=target_selection,
                    source=source_text,
                    config_location=target_location,
                    import_name=import_name,
                )
            )

    resolved_sources.extend(
        _resolve_companion_sources(
            config.companions,
            request.case,
            execution_root=execution_root,
            shared=shared,
            key_prefix=key_prefix,
            import_name=import_name,
        )
    )

    return tuple(resolved_sources)


def _resolve_import_root(spec: ConfigurationImport, manifest: Path) -> Path:
    candidate = manifest.parent / Path(spec.root)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(
            f"import {spec.name!r} root does not exist: {candidate}"
        ) from exc
    if not resolved.is_dir():
        raise SelectionError(f"import {spec.name!r} root is not a directory: {candidate}")
    return resolved


def _load_imported_config(spec: ConfigurationImport, import_root: Path) -> Config:
    candidate = import_root / Path(spec.configuration)
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"import {spec.name!r} configuration was not found: {candidate}"
        ) from exc
    if not resolved.is_file():
        raise ConfigurationError(
            f"import {spec.name!r} configuration is not a regular file: {candidate}"
        )
    if not _is_within(resolved, import_root):
        raise ConfigurationError(
            f"import {spec.name!r} configuration resolves outside its import root: {resolved}"
        )

    try:
        imported = load_config(resolved)
    except ConfigurationError as exc:
        raise ConfigurationError(
            f"import {spec.name!r} configuration is invalid: {exc}"
        ) from exc
    if imported.imports:
        raise ConfigurationError(
            f"import {spec.name!r} configuration must not declare [import.<name>] in 0.4.0"
        )
    return imported


def resolve_sources(
    config: Config,
    request: BuildRequest,
    *,
    cwd: str | Path | None = None,
) -> tuple[ResolvedSource, ...]:
    """Resolve Root-local sources plus every explicitly imported Configuration."""

    cwd_path = Path.cwd().resolve() if cwd is None else Path(cwd).expanduser().resolve(strict=True)
    if not cwd_path.is_dir():
        raise SelectionError(f"current working directory is not a directory: {cwd_path}")

    _validate_request(config, request)

    loaded_imports: dict[str, tuple[ConfigurationImport, Path, Config]] = {}
    imported_shared: dict[str, SharedPatterns] = {}
    for name in sorted(config.imports):
        spec = config.imports[name]
        import_root = _resolve_import_root(spec, config.manifest)
        imported = _load_imported_config(spec, import_root)
        loaded_imports[name] = (spec, import_root, imported)
        imported_shared[name] = imported.shared

    root_visible_shared = _merge_root_visible_shared(
        config.shared,
        imported_shared,
        where=f"{config.manifest} [shared]",
    )

    resolved_sources = list(
        _resolve_configuration_sources(
            config,
            request,
            execution_root=cwd_path,
            shared=root_visible_shared,
        )
    )

    for name in sorted(loaded_imports):
        spec, import_root, imported = loaded_imports[name]
        duplicate_names = sorted(set(imported.companions) & set(spec.companions))
        if duplicate_names:
            listed = ", ".join(f"{name}.{companion}" for companion in duplicate_names)
            raise ConfigurationError(
                f"import {name!r} defines duplicate companion logical name(s): {listed}"
            )
        if not imported.companions and not spec.companions:
            raise ConfigurationError(
                f"import {name!r} must provide at least one companion either from "
                "the imported Configuration or [import.<name>.companion.<name>]"
            )
        try:
            _validate_import_companion_case(
                imported.companions, spec.companions, spec.case
            )
            imported_sources = _resolve_companion_sources(
                imported.companions,
                spec.case,
                execution_root=import_root,
                shared=imported.shared,
                key_prefix=f"import:{name}:imported:",
                import_name=name,
            )
            added_sources = _resolve_companion_sources(
                spec.companions,
                spec.case,
                execution_root=import_root,
                shared=root_visible_shared,
                key_prefix=f"import:{name}:added:",
                import_name=name,
                config_location_prefix=f"import.{name}.companion",
                allow_execution_root=True,
            )
        except SelectionError as exc:
            raise SelectionError(f"import {name!r}: {exc}") from exc
        resolved_sources.extend(imported_sources)
        resolved_sources.extend(added_sources)

    return tuple(resolved_sources)

def _name_matches(name: str, pattern: ExclusionPattern) -> bool:
    if pattern.match == "exact":
        return name == pattern.value
    if pattern.match == "prefix":
        return name.startswith(pattern.value)
    if pattern.match == "suffix":
        return name.endswith(pattern.value)
    if pattern.match == "contains":
        return pattern.value in name
    raise AssertionError(f"unknown exclusion match kind: {pattern.match}")


def _file_is_excluded(relative: str, exclusions: tuple[ExclusionPattern, ...]) -> bool:
    path = PurePosixPath(relative)
    directory_names = path.parts[:-1]
    for pattern in exclusions:
        if pattern.directory:
            if any(_name_matches(name, pattern) for name in directory_names):
                return True
        elif _name_matches(path.name, pattern):
            return True
    return False


def _files_under_entry(
    entry: Path,
    *,
    root: Path,
    source_label: str,
) -> tuple[Path, ...]:
    """Collect files below one selected entry without following directory symlinks."""

    root_resolved = root.resolve()

    if entry.is_symlink() and entry.is_dir():
        resolved = entry.resolve()
        if not _is_within(resolved, root_resolved):
            raise SelectionError(
                f"selection for {source_label} encounters a directory symlink outside its directory: {entry}"
            )
        return ()

    if entry.is_file():
        return (entry,)
    if not entry.is_dir():
        return ()

    files: list[Path] = []

    def walk(directory: Path) -> None:
        try:
            children = sorted(directory.iterdir(), key=lambda path: path.name)
        except OSError as exc:
            raise SelectionError(
                f"cannot inspect selected directory for {source_label}: {directory}"
            ) from exc

        for child in children:
            if child.is_symlink() and child.is_dir():
                resolved = child.resolve()
                if not _is_within(resolved, root_resolved):
                    raise SelectionError(
                        f"selection for {source_label} encounters a directory symlink outside its directory: {child}"
                    )
                continue
            if child.is_dir():
                walk(child)
            elif child.is_file():
                files.append(child)

    walk(entry)
    return tuple(files)


def _include_name_matches(name: str, pattern: str) -> bool:
    if "*" not in pattern:
        return name == pattern
    prefix, suffix = pattern.split("*", 1)
    return (
        name.startswith(prefix)
        and name.endswith(suffix)
        and len(name) >= len(prefix) + len(suffix)
    )


def _matching_include_entries(root: Path, pattern: str) -> tuple[Path, ...]:
    """Resolve one include pattern without recursive wildcards."""

    root_resolved = root.resolve()
    candidates: tuple[Path, ...] = (root,)
    parts = PurePosixPath(pattern).parts
    for index, part in enumerate(parts):
        last = index == len(parts) - 1
        next_candidates: list[Path] = []
        for parent in candidates:
            parent_resolved = parent.resolve()
            if not _is_within(parent_resolved, root_resolved):
                raise SelectionError(
                    f"include pattern {pattern!r} traverses outside its directory through a symlink: {parent}"
                )
            if not parent.is_dir():
                continue
            try:
                children = tuple(parent.iterdir())
            except OSError as exc:
                raise SelectionError(
                    f"cannot inspect directory while matching include {pattern!r}: {parent}"
                ) from exc

            if "*" not in part:
                for child in children:
                    if child.name == part:
                        next_candidates.append(child)
                continue

            for child in children:
                if _include_name_matches(child.name, part):
                    next_candidates.append(child)

        checked: list[Path] = []
        for candidate in next_candidates:
            resolved = candidate.resolve()
            if not _is_within(resolved, root_resolved):
                raise SelectionError(
                    f"include pattern {pattern!r} selects an entry outside its directory through a symlink: {candidate}"
                )
            if last or candidate.is_dir():
                checked.append(candidate)
        candidates = tuple(checked)
        if not candidates:
            break
    return tuple(sorted(candidates, key=lambda path: path.as_posix()))


def select_files(source: ResolvedSource, *, allow_missing: bool = False) -> SelectionResult:
    """Select files using required and optional include patterns plus name exclusions."""

    selected: dict[str, Path] = {}
    missing: list[str] = []
    optional_missing: list[str] = []
    root = source.directory
    root_resolved = root.resolve()
    selection = source.selection

    def collect_pattern(relative_include: str, *, optional: bool) -> None:
        entries = _matching_include_entries(root, relative_include)
        if not entries:
            (optional_missing if optional else missing).append(relative_include)
            return

        for entry in entries:
            entry_resolved = entry.resolve()
            if not _is_within(entry_resolved, root_resolved):
                raise SelectionError(
                    f"selection for {source.label} selects an entry outside its directory through a symlink: {entry}"
                )
            if not entry.is_file() and not entry.is_dir():
                raise SelectionError(
                    f"selection for {source.label} selects an unsupported filesystem entry: {entry}"
                )

            for candidate in _files_under_entry(
                entry,
                root=root,
                source_label=source.label,
            ):
                relative = candidate.relative_to(root).as_posix()
                if _file_is_excluded(relative, selection.exclude):
                    continue
                resolved = candidate.resolve()
                if not _is_within(resolved, root_resolved):
                    raise SelectionError(
                        f"selection for {source.label} selects a file outside its directory through a symlink: {candidate}"
                    )
                selected[relative] = candidate

    for relative_include in selection.include:
        collect_pattern(relative_include, optional=False)
    for relative_include in selection.include_if_exists:
        collect_pattern(relative_include, optional=True)

    if missing and not allow_missing:
        listed = ", ".join(repr(path) for path in missing)
        raise SelectionError(
            f"{source.label} has include pattern(s) with no matches: {listed}"
        )

    return SelectionResult(
        files=tuple(selected[key] for key in sorted(selected)),
        missing=tuple(sorted(set(missing))),
        optional_missing=tuple(sorted(set(optional_missing))),
    )


def collect_files(source: ResolvedSource) -> tuple[Path, ...]:
    """Collect files for one resolved source, requiring every include to match."""

    return select_files(source).files


def _render_archive_readme(
    config: Config,
    request: BuildRequest,
    sources: tuple[ResolvedSource, ...],
    selection_counts: Mapping[str, int],
) -> str:
    """Render the archive-root README from declared descriptions and resolved facts."""

    grouped: dict[str, list[ResolvedSource]] = {}
    for source in sources:
        grouped.setdefault(source.archive_root, []).append(source)

    selected_case = request.case if request.case is not None else "default"
    lines = [
        "# Archive contents",
        "",
        "## Root Configuration",
        "",
        "- Execution root: `.`",
        f"- Case: `{selected_case}`",
        "",
    ]

    if config.imports:
        lines.extend(["## Configuration imports", ""])
        for name in sorted(config.imports):
            spec = config.imports[name]
            imported_case = spec.case if spec.case is not None else "default"
            lines.extend([
                f"### `{name}`",
                "",
                f"- Execution root: `{spec.root}`",
                f"- Configuration: `{spec.configuration}`",
                f"- Case: `{imported_case}`",
            ])
            lines.append("")

    lines.extend(["## Included directories", ""])

    for archive_root in sorted(grouped):
        lines.extend([f"### `{archive_root}/`", ""])
        source_group = sorted(grouped[archive_root], key=lambda item: item.key)
        for source in source_group:
            count = selection_counts[source.key]
            if source.kind == "target":
                heading = "#### Target"
            else:
                heading = f"#### Companion `{source.name}`"
            lines.extend([heading, "", source.description, ""])
            if source.import_name is not None:
                lines.append(f"- Import: `{source.import_name}`")
            lines.extend([
                f"- Configuration: `{source.config_location}`",
                f"- Directory source: {source.source}",
                f"- Selected files: {count}",
            ])
            if count == 0:
                lines.append(f"- Empty result policy: `{source.selection.if_empty}`")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"

def plan_archive(
    config: Config,
    request: BuildRequest,
    *,
    cwd: str | Path | None = None,
    allow_missing: bool = False,
) -> ArchivePlan:
    """Resolve archive entries without writing an archive."""

    cwd_path = Path.cwd().resolve() if cwd is None else Path(cwd).expanduser().resolve(strict=True)
    sources = resolve_sources(config, request, cwd=cwd_path)

    archive_entries: dict[str, Path] = {}
    physical_entries: dict[Path, str] = {}
    missing_entries: list[str] = []
    optional_missing_entries: list[str] = []
    empty_selections: list[EmptySelectionStatus] = []
    selection_counts: dict[str, int] = {}

    for source in sources:
        result = select_files(source, allow_missing=allow_missing)
        selection_counts[source.key] = len(result.files)
        for relative in result.missing:
            missing_entries.append(f"{source.archive_root}/{relative}")
        for relative in result.optional_missing:
            optional_missing_entries.append(f"{source.archive_root}/{relative}")

        if not result.files:
            empty_selections.append(
                EmptySelectionStatus(
                    key=source.key,
                    label=source.label,
                    archive_root=source.archive_root,
                    if_empty=source.selection.if_empty,
                )
            )
            if source.selection.if_empty == "error" and not allow_missing:
                raise SelectionError(
                    f"{source.label} selected no files and if_empty is 'error'"
                )

        for file in result.files:
            relative = file.relative_to(source.directory).as_posix()
            arcname = f"{source.archive_root}/{relative}"
            source_resolved = file.resolve()
            previous = archive_entries.get(arcname)
            if previous is not None and previous.resolve() != source_resolved:
                raise SelectionError(
                    f"multiple files resolve to the same archive path {arcname!r}: {previous} and {file}"
                )
            previous_arcname = physical_entries.get(source_resolved)
            if previous_arcname is not None and previous_arcname != arcname:
                raise SelectionError(
                    f"the same physical file resolves to different archive paths {previous_arcname!r} and {arcname!r}: {file}"
                )
            archive_entries[arcname] = file
            physical_entries[source_resolved] = arcname

    empty_directories = sorted({
        status.archive_root
        for status in empty_selections
        if status.if_empty == "allow"
        and not any(arcname.startswith(f"{status.archive_root}/") for arcname in archive_entries)
    })

    readme = _render_archive_readme(config, request, sources, selection_counts)
    return ArchivePlan(
        entries=MappingProxyType(dict(sorted(archive_entries.items()))),
        readme=readme,
        missing=tuple(sorted(set(missing_entries))),
        optional_missing=tuple(sorted(set(optional_missing_entries))),
        empty_directories=tuple(empty_directories),
        empty_selections=tuple(sorted(empty_selections, key=lambda item: item.key)),
    )


def render_archive_tree(
    plan: ArchivePlan | Mapping[str, Path] | tuple[str, ...] | list[str],
) -> str:
    """Render archive entry paths as a deterministic tree, marking missing paths."""

    if isinstance(plan, ArchivePlan):
        empty_roots = {status.archive_root for status in plan.empty_selections}
        directory_paths = set(plan.empty_directories) | empty_roots
        paths = [
            "README.md",
            *plan.entries.keys(),
            *plan.missing,
            *plan.optional_missing,
            *directory_paths,
        ]
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
            outcome = "allowed" if status.if_empty == "allow" else "would error"
            lines.append(f"- {status.label} (`{status.archive_root}/`): empty, {outcome}")
    return "\n".join(lines)


def _current_output_timestamp() -> str:
    """Return the local process time used once for one generated output name."""

    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _resolve_output_path(
    config: Config,
    request: BuildRequest,
    cwd: Path,
) -> tuple[Path, str]:
    output = config.output
    if output.generated:
        assert output.directory is not None
        parts: list[str] = []
        if output.prefix is not None:
            parts.append(output.prefix)
        parts.append(_current_output_timestamp())
        if request.sequence is not None:
            parts.append(str(request.sequence))
        if output.suffix is not None:
            parts.append(output.suffix)
        candidate = cwd / Path(output.directory) / ("-".join(parts) + ".zip")
        if_exists = "error"
    else:
        assert output.path is not None
        assert output.if_exists is not None
        candidate = cwd / Path(output.path)
        if_exists = output.if_exists

    if candidate.is_symlink():
        raise SelectionError(f"output path must not be a symbolic link: {candidate}")
    resolved = candidate.resolve(strict=False)
    if not _is_within(resolved, cwd):
        raise SelectionError(
            f"output path must stay below the current working directory: {resolved}"
        )
    if candidate.exists() and candidate.is_dir():
        raise SelectionError(f"output path is a directory: {candidate}")
    return candidate, if_exists


def build_archive(
    config: Config,
    request: BuildRequest,
    *,
    cwd: str | Path | None = None,
) -> Path:
    """Build one ZIP archive using the output policy declared by the configuration."""

    cwd_path = Path.cwd().resolve() if cwd is None else Path(cwd).expanduser().resolve(strict=True)
    _validate_request(config, request)
    output_path, if_exists = _resolve_output_path(config, request, cwd_path)

    if output_path.exists() and if_exists == "error":
        raise SelectionError(f"output archive already exists: {output_path}")

    plan = plan_archive(config, request, cwd=cwd_path)
    archive_entries = plan.entries
    output_resolved = output_path.resolve(strict=False)
    if any(path.resolve() == output_resolved for path in archive_entries.values()):
        raise SelectionError(f"output archive is selected as an input file: {output_path}")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SelectionError(f"cannot create output directory: {output_path.parent}") from exc
    parent_resolved = output_path.parent.resolve(strict=True)
    if not _is_within(parent_resolved, cwd_path):
        raise SelectionError(
            f"output directory must stay below the current working directory: {parent_resolved}"
        )

    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_path.parent,
            delete=False,
        ) as handle:
            temporary = Path(handle.name)

        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("README.md", plan.readme)
            for directory in plan.empty_directories:
                archive.writestr(f"{directory.rstrip('/')}/", b"")
            for arcname, source in archive_entries.items():
                archive.write(source, arcname=arcname)

        if if_exists == "error" and output_path.exists():
            raise SelectionError(f"output archive already exists: {output_path}")
        try:
            os.replace(temporary, output_path)
        except OSError as exc:
            raise SelectionError(f"cannot finalize output archive: {output_path}") from exc
        temporary = None
        return output_path
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

"""Directory resolution, file selection, archive planning, and ZIP creation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
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
    Target,
    TargetSkipPattern,
    _materialize_selection,
    load_config,
)
from .errors import ConfigurationError, SelectionError


@dataclass(frozen=True)
class BuildRequest:
    """One build request with Target references, one Case, output sequence, and README options."""

    directories: tuple[str, ...] = ()
    case: str | None = None
    sequence: int | None = None
    paths: bool = False

    @classmethod
    def create(
        cls,
        *directories: str | Path,
        case: str | None = None,
        sequence: int | None = None,
        paths: bool = False,
    ) -> "BuildRequest":
        normalized_directories: list[str] = []
        for directory in directories:
            if isinstance(directory, Path):
                normalized_directories.append(directory.as_posix())
            else:
                normalized_directories.append(str(directory))
        return cls(
            directories=tuple(normalized_directories),
            case=case,
            sequence=sequence,
            paths=paths,
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


@dataclass(frozen=True)
class _ConfigurationLayer:
    """One loaded Configuration and the execution root established for it."""

    config: Config
    execution_root: Path
    import_name: str | None


@dataclass(frozen=True)
class _TargetBinding:
    """The effective Target together with the layer that owns it."""

    target: Target
    layer: _ConfigurationLayer


@dataclass(frozen=True)
class _CompanionBinding:
    """One effective Companion plus the root against which its path is resolved."""

    companion: Companion
    layer: _ConfigurationLayer
    execution_root: Path
    config_location_prefix: str


@dataclass(frozen=True)
class _EffectiveConfiguration:
    """Definitions remaining after one linear Configuration chain is layered."""

    root: Config
    layers: tuple[_ConfigurationLayer, ...]
    about_description: str | None
    shared: SharedPatterns
    target: _TargetBinding | None
    companions: Mapping[str, _CompanionBinding]


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _target_name_matches(name: str, pattern: TargetSkipPattern) -> bool:
    if pattern.match == "exact":
        return name == pattern.value
    if pattern.match == "prefix":
        return name.startswith(pattern.value)
    if pattern.match == "suffix":
        return name.endswith(pattern.value)
    if pattern.match == "contains":
        return pattern.value in name
    raise AssertionError(f"unknown Target skip match kind: {pattern.match}")


def _target_is_skipped(name: str, patterns: tuple[TargetSkipPattern, ...]) -> bool:
    return any(_target_name_matches(name, pattern) for pattern in patterns)


def _validate_target_name(name: str, *, label: str) -> None:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise SelectionError(
            f"{label} must name one direct child directory: {name!r}"
        )


def _resolve_target_directory(
    name: str,
    base: Path,
    *,
    label: str,
) -> tuple[Path, str]:
    _validate_target_name(name, label=label)
    candidate = base / name
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{label} does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise SelectionError(f"{label} is not a directory: {candidate}")

    base_resolved = base.resolve()
    try:
        relative = resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise SelectionError(
            f"{label} resolves outside its Target resolution base: {resolved}"
        ) from exc

    if len(relative.parts) != 1:
        raise SelectionError(
            f"{label} must resolve to a direct child directory of its Target resolution base: {resolved}"
        )
    return resolved, relative.as_posix()


def _resolve_target_location(path: str, base: Path, *, name: str) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(
            f"target location {name!r} does not exist: {candidate}"
        ) from exc
    if not resolved.is_dir():
        raise SelectionError(
            f"target location {name!r} is not a directory: {candidate}"
        )
    return resolved


def _target_reference_is_absolute(reference: str) -> bool:
    pure = PurePosixPath(reference)
    windows = PureWindowsPath(reference)
    return pure.is_absolute() or windows.is_absolute() or bool(windows.drive)


def _location_expansion_name(reference: str) -> str | None:
    if not reference.endswith("/"):
        return None
    candidate = reference[:-1]
    if not candidate or "/" in candidate or candidate in {".", ".."}:
        return None
    return candidate


def _expand_target_location(
    name: str,
    location_root: Path,
    skip: tuple[TargetSkipPattern, ...],
) -> tuple[tuple[Path, str], ...]:
    resolved_root = location_root.resolve()
    targets: list[tuple[Path, str]] = []
    for entry in sorted(location_root.iterdir(), key=lambda item: item.name):
        if _target_is_skipped(entry.name, skip):
            continue
        if entry.is_symlink():
            try:
                resolved_entry = entry.resolve(strict=True)
            except FileNotFoundError as exc:
                raise SelectionError(
                    f"target location {name!r} contains a broken symbolic link: {entry}"
                ) from exc
            if resolved_entry.is_dir() and not _is_within(resolved_entry, resolved_root):
                raise SelectionError(
                    f"target location {name!r} contains a directory symbolic link outside its boundary: {entry}"
                )
        if not entry.is_dir():
            continue
        directory, archive_root = _resolve_target_directory(
            entry.name,
            location_root,
            label=f"target from location {name!r}",
        )
        targets.append((directory, archive_root))

    if not targets:
        raise SelectionError(
            f"target location {name!r} contains no eligible direct child directories"
        )
    return tuple(targets)


def _resolve_target_reference(
    reference: str,
    binding: _TargetBinding,
    cwd: Path,
    *,
    label: str,
) -> tuple[tuple[Path, str], ...]:
    if not reference:
        raise SelectionError(f"{label} must not be empty")
    if "\\" in reference:
        raise SelectionError(
            f"{label} must use '/' as the path separator: {reference!r}"
        )
    if _target_reference_is_absolute(reference):
        raise SelectionError(
            f"{label} must be relative; use a Target location for Targets outside cwd: {reference!r}"
        )

    expansion = _location_expansion_name(reference)
    if expansion is not None:
        location = binding.target.locations.get(expansion)
        if location is None:
            raise SelectionError(f"target location {expansion!r} is not defined")
        location_root = _resolve_target_location(
            location.path,
            binding.layer.execution_root,
            name=expansion,
        )
        return _expand_target_location(expansion, location_root, location.skip)

    if reference.endswith("/"):
        raise SelectionError(
            f"{label} must use NAME, LOCATION/NAME, or LOCATION/: {reference!r}"
        )

    parts = reference.split("/")
    if len(parts) == 1:
        name = parts[0]
        _validate_target_name(name, label=label)
        if _target_is_skipped(name, binding.target.skip):
            raise SelectionError(f"{label} is skipped by [target].skip: {name!r}")
        return (_resolve_target_directory(name, cwd, label=label),)

    if len(parts) == 2 and all(parts):
        location_name, name = parts
        _validate_target_name(location_name, label="target location name")
        _validate_target_name(name, label=label)
        location = binding.target.locations.get(location_name)
        if location is None:
            raise SelectionError(f"target location {location_name!r} is not defined")
        if _target_is_skipped(name, location.skip):
            raise SelectionError(
                f"{label} is skipped by [target.location.{location_name}].skip: {name!r}"
            )
        location_root = _resolve_target_location(
            location.path,
            binding.layer.execution_root,
            name=location_name,
        )
        return (_resolve_target_directory(name, location_root, label=label),)

    raise SelectionError(
        f"{label} must use NAME, LOCATION/NAME, or LOCATION/: {reference!r}"
    )


def _resolve_companion_directory(
    path: str | Path,
    base: Path,
    *,
    label: str,
) -> tuple[Path, str]:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = base / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{label} does not exist: {candidate}") from exc
    if not resolved.is_dir():
        raise SelectionError(f"{label} is not a directory: {candidate}")
    if resolved.parent == resolved:
        raise SelectionError(f"{label} cannot use the filesystem root as a source directory")

    try:
        relative = resolved.relative_to(base.resolve())
    except ValueError:
        return resolved, resolved.name

    if relative == Path("."):
        return resolved, resolved.name
    return resolved, relative.as_posix()


def _resolve_import_root(spec: ConfigurationImport, manifest: Path) -> Path:
    candidate = Path(spec.root)
    if not candidate.is_absolute():
        candidate = manifest.parent / candidate
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
        return load_config(resolved)
    except ConfigurationError as exc:
        raise ConfigurationError(
            f"import {spec.name!r} configuration is invalid: {exc}"
        ) from exc


def _single_import(config: Config) -> ConfigurationImport | None:
    if not config.imports:
        return None
    if len(config.imports) != 1:
        # load_config already rejects this; keep the invariant explicit here.
        raise ConfigurationError(
            f"{config.manifest}: each Configuration may define at most one import"
        )
    return next(iter(config.imports.values()))


def _configuration_chain(config: Config, cwd: Path) -> tuple[_ConfigurationLayer, ...]:
    """Load one unbounded linear import chain and reject cycles by real path."""

    layers: list[_ConfigurationLayer] = []
    active_paths: list[Path] = []
    current = config
    execution_root = cwd
    import_name: str | None = None

    while True:
        manifest = current.manifest.resolve()
        if manifest in active_paths:
            start = active_paths.index(manifest)
            cycle = [*active_paths[start:], manifest]
            rendered = " -> ".join(str(path) for path in cycle)
            raise ConfigurationError(f"configuration import cycle detected: {rendered}")

        active_paths.append(manifest)
        layers.append(
            _ConfigurationLayer(
                config=current,
                execution_root=execution_root,
                import_name=import_name,
            )
        )

        spec = _single_import(current)
        if spec is None:
            break
        execution_root = _resolve_import_root(spec, current.manifest)
        current = _load_imported_config(spec, execution_root)
        import_name = spec.name

    return tuple(layers)


def _compose_shared(layers: tuple[_ConfigurationLayer, ...]) -> SharedPatterns:
    include: dict[str, tuple[str, ...]] = {}
    exclude: dict[str, tuple[ExclusionPattern, ...]] = {}
    for layer in reversed(layers):
        include.update(layer.config.shared.include)
        exclude.update(layer.config.shared.exclude)
    return SharedPatterns(
        include=MappingProxyType(include),
        exclude=MappingProxyType(exclude),
    )


def _compose_effective_configuration(
    config: Config,
    cwd: Path,
) -> _EffectiveConfiguration:
    layers = _configuration_chain(config, cwd)
    about_description = next(
        (layer.config.about_description for layer in layers if layer.config.about_description is not None),
        None,
    )
    shared = _compose_shared(layers)
    target: _TargetBinding | None = None
    companions: dict[str, _CompanionBinding] = {}

    # Start at the deepest layer; each outer definition then shadows by name.
    for index in range(len(layers) - 1, -1, -1):
        layer = layers[index]
        current = layer.config
        if current.target is not None:
            target = _TargetBinding(current.target, layer)

        for name, companion in current.companions.items():
            companions[name] = _CompanionBinding(
                companion=companion,
                layer=layer,
                execution_root=layer.execution_root,
                config_location_prefix="companion",
            )

        spec = _single_import(current)
        if spec is not None:
            if index + 1 >= len(layers):
                raise AssertionError("import link has no loaded child layer")
            import_root = layers[index + 1].execution_root
            for name, companion in spec.companions.items():
                companions[name] = _CompanionBinding(
                    companion=companion,
                    layer=layer,
                    execution_root=import_root,
                    config_location_prefix=f"import.{spec.name}.companion",
                )

    if target is None and not companions:
        raise ConfigurationError(
            f"{config.manifest}: the resolved Configuration chain defines no Target or Companion"
        )

    effective = _EffectiveConfiguration(
        root=config,
        layers=layers,
        about_description=about_description,
        shared=shared,
        target=target,
        companions=MappingProxyType(dict(companions)),
    )
    _validate_effective_configuration(effective)
    return effective


def _validate_target_selections(binding: _TargetBinding, shared: SharedPatterns) -> None:
    target = binding.target
    if target.default is not None:
        _materialize_selection(target.default, shared, "[target]")
    for name, selection in target.cases.items():
        _materialize_selection(selection, shared, f"[target.case.{name}]")


def _validate_companion_selections(
    binding: _CompanionBinding,
    shared: SharedPatterns,
) -> None:
    companion = binding.companion
    prefix = binding.config_location_prefix
    _materialize_selection(companion.selection, shared, f"[{prefix}.{companion.name}]")
    for name, selection in companion.cases.items():
        _materialize_selection(
            selection,
            shared,
            f"[{prefix}.{companion.name}.case.{name}]",
        )


def _validate_effective_configuration(effective: _EffectiveConfiguration) -> None:
    if effective.target is not None:
        _validate_target_selections(effective.target, effective.shared)
        target_cases = set(effective.target.target.cases)
        for name, binding in effective.companions.items():
            unreachable = sorted(set(binding.companion.cases) - target_cases)
            if unreachable:
                listed = ", ".join(repr(case) for case in unreachable)
                raise ConfigurationError(
                    f"effective [companion.{name}.case]: case(s) not defined by target: {listed}"
                )
    for binding in effective.companions.values():
        _validate_companion_selections(binding, effective.shared)


def _available_cases(effective: _EffectiveConfiguration) -> tuple[str, ...]:
    if effective.target is not None:
        return tuple(sorted(effective.target.target.cases))
    return tuple(sorted({
        case
        for binding in effective.companions.values()
        for case in binding.companion.cases
    }))


def _validate_request(
    effective: _EffectiveConfiguration,
    request: BuildRequest,
) -> None:
    output = effective.root.output
    if request.sequence is not None:
        if isinstance(request.sequence, bool) or not isinstance(request.sequence, int) or request.sequence < 1:
            raise SelectionError("output sequence must be an integer greater than or equal to 1")
        if not output.generated:
            raise SelectionError("output sequence can only be used with generated output")

    if effective.target is None:
        if request.directories:
            raise SelectionError(
                "the effective Configuration does not define a Target; TARGET must not be specified"
            )
    elif not request.directories:
        raise SelectionError(
            "TARGET is required when the effective Configuration defines a Target (one or more may be specified)"
        )

    if request.case is None:
        return
    available = _available_cases(effective)
    if request.case not in available:
        listed = ", ".join(available) or "(none)"
        raise SelectionError(
            f"case {request.case!r} is not defined; available cases: {listed}"
        )


def _selected_target(
    binding: _TargetBinding,
    case: str | None,
    *,
    shared: SharedPatterns,
) -> tuple[Selection, str]:
    target = binding.target
    if case is None:
        if target.default is None:
            available = ", ".join(sorted(target.cases)) or "(none)"
            raise SelectionError(
                "the effective Target has no default [target]; "
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
    binding: _CompanionBinding,
    case: str | None,
    *,
    shared: SharedPatterns,
) -> tuple[Selection, str]:
    companion = binding.companion
    prefix = binding.config_location_prefix
    if case is not None and case in companion.cases:
        location = f"[{prefix}.{companion.name}.case.{case}]"
        return _materialize_selection(companion.cases[case], shared, location), location
    location = f"[{prefix}.{companion.name}]"
    return _materialize_selection(companion.selection, shared, location), location


def _resolve_effective_sources(
    effective: _EffectiveConfiguration,
    request: BuildRequest,
) -> tuple[ResolvedSource, ...]:
    _validate_request(effective, request)
    resolved: list[ResolvedSource] = []

    if effective.target is not None:
        selection, location = _selected_target(
            effective.target,
            request.case,
            shared=effective.shared,
        )
        runtime_targets: list[tuple[Path, str]] = []
        seen: set[Path] = set()
        reference_count = len(request.directories)
        for index, requested in enumerate(request.directories, start=1):
            label = f"target reference {index}" if reference_count > 1 else "target reference"
            for directory, archive_root in _resolve_target_reference(
                requested,
                effective.target,
                effective.layers[0].execution_root,
                label=label,
            ):
                if directory in seen:
                    raise SelectionError(
                        f"target directories must resolve to distinct directories: {directory}"
                    )
                seen.add(directory)
                runtime_targets.append((directory, archive_root))

        target_count = len(runtime_targets)
        for index, (directory, archive_root) in enumerate(runtime_targets, start=1):
            key = "target" if target_count == 1 else f"target:{index}"
            name = None if target_count == 1 else archive_root
            resolved.append(
                ResolvedSource(
                    key=key,
                    kind="target",
                    name=name,
                    description=selection.description,
                    directory=directory,
                    archive_root=archive_root,
                    selection=selection,
                )
            )

    for name, binding in effective.companions.items():
        selection, location = _selected_companion(
            binding,
            request.case,
            shared=effective.shared,
        )
        directory, archive_root = _resolve_companion_directory(
            binding.companion.path,
            binding.execution_root,
            label=f"companion {name!r}",
        )
        resolved.append(
            ResolvedSource(
                key=f"companion:{name}",
                kind="companion",
                name=name,
                description=selection.description,
                directory=directory,
                archive_root=archive_root,
                selection=selection,
            )
        )

    return tuple(resolved)


def _resolve_execution(
    config: Config,
    request: BuildRequest,
    *,
    cwd: Path,
) -> tuple[_EffectiveConfiguration, tuple[ResolvedSource, ...]]:
    effective = _compose_effective_configuration(config, cwd)
    return effective, _resolve_effective_sources(effective, request)


def resolve_sources(
    config: Config,
    request: BuildRequest,
    *,
    cwd: str | Path | None = None,
) -> tuple[ResolvedSource, ...]:
    """Resolve sources from one layered Effective Configuration."""

    cwd_path = Path.cwd().resolve() if cwd is None else Path(cwd).expanduser().resolve(strict=True)
    if not cwd_path.is_dir():
        raise SelectionError(f"current working directory is not a directory: {cwd_path}")
    _, sources = _resolve_execution(config, request, cwd=cwd_path)
    return sources

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


def _archive_index_cell(value: str) -> str:
    """Escape one value for the generated Markdown index table."""

    return value.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>").replace("|", "\\|")


def _render_archive_readme(
    request: BuildRequest,
    about_description: str | None,
    sources: tuple[ResolvedSource, ...],
    selection_counts: Mapping[str, int],
) -> str:
    """Render the archive-root README as a content index."""

    headers = ["Path", "Description", "Files"]
    alignments = ["---", "---", "---:"]
    if request.paths:
        headers.append("Source")
        alignments.append("---")

    lines = ["# Archive contents", ""]
    if about_description is not None:
        lines.extend([about_description, ""])
    lines.extend([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(alignments) + " |",
    ])

    for source in sorted(sources, key=lambda item: (item.archive_root, item.key)):
        row = [
            _archive_index_cell(f"{source.archive_root.rstrip('/')}/"),
            _archive_index_cell(source.description),
            str(selection_counts[source.key]),
        ]
        if request.paths:
            row.append(_archive_index_cell(source.directory.as_posix()))
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines) + "\n"

def plan_archive(
    config: Config,
    request: BuildRequest,
    *,
    cwd: str | Path | None = None,
    allow_missing: bool = False,
) -> ArchivePlan:
    """Resolve archive entries without writing an archive."""

    cwd_path = Path.cwd().resolve() if cwd is None else Path(cwd).expanduser().resolve(strict=True)
    if not cwd_path.is_dir():
        raise SelectionError(f"current working directory is not a directory: {cwd_path}")
    effective, sources = _resolve_execution(config, request, cwd=cwd_path)

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

    readme = _render_archive_readme(
        request,
        effective.about_description,
        sources,
        selection_counts,
    )
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
        directory = Path(output.directory)
        if not directory.is_absolute():
            directory = cwd / directory
        candidate = directory / ("-".join(parts) + ".zip")
        if_exists = "error"
    else:
        assert output.path is not None
        assert output.if_exists is not None
        candidate = Path(output.path)
        if not candidate.is_absolute():
            candidate = cwd / candidate
        if_exists = output.if_exists

    if candidate.is_symlink():
        raise SelectionError(f"output path must not be a symbolic link: {candidate}")
    candidate = candidate.resolve(strict=False)
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
    if request.sequence is not None:
        if isinstance(request.sequence, bool) or not isinstance(request.sequence, int) or request.sequence < 1:
            raise SelectionError("output sequence must be an integer greater than or equal to 1")
        if not config.output.generated:
            raise SelectionError("output sequence can only be used with generated output")
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

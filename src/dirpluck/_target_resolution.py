"""Filesystem resolution for normalized Target requests."""

from __future__ import annotations

from pathlib import Path

from ._filesystem import safe_is_link_like
from ._extraction_spec import BoundTargetSpec, TargetRootSpec
from ._resolution_models import ResolvedTarget
from ._target_models import (
    TargetIgnorePattern,
    TargetEntryExpr,
    TargetEntryKind,
    TargetKind,
    TargetListExpr,
    TargetRegexExpr,
    TargetScopeExpr,
    validate_target_name,
)
from .errors import SelectionError


def _archive_root(source_root: str, archive_prefix: str | None) -> str:
    return source_root if archive_prefix is None else f"{archive_prefix}/{source_root}"


def _target_is_ignored(
    name: str,
    *,
    directory: bool,
    patterns: tuple[TargetIgnorePattern, ...],
) -> bool:
    return any(pattern.matches(name, directory=directory) for pattern in patterns)


def _resolve_target_directory(name: str, root: Path, *, label: str) -> tuple[Path, str]:
    validate_target_name(name, label=label)
    candidate = root / name
    if safe_is_link_like(candidate):
        raise SelectionError(
            f"{label} is a symbolic link or Windows junction and is not a selectable Target: {candidate}"
        )
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{label} does not exist: {candidate}") from exc
    if not resolved.is_dir():
        if resolved.is_file():
            raise SelectionError(
                f"{label} is not a directory: {candidate}; a regular file exists at that name, "
                + "so remove the trailing '/' if the file was intended"
            )
        raise SelectionError(f"{label} is not a directory: {candidate}")
    root_resolved = root.resolve()
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SelectionError(f"{label} resolves outside its Scope root: {resolved}") from exc
    if len(relative.parts) != 1:
        raise SelectionError(
            f"{label} must resolve to a direct child directory of its Scope root: {resolved}"
        )
    return resolved, relative.as_posix()


def _resolve_target_file(name: str, root: Path, *, label: str) -> tuple[Path, str]:
    validate_target_name(name, label=label, target_kind="file")
    candidate = root / name
    if safe_is_link_like(candidate):
        raise SelectionError(
            f"{label} is a symbolic link or Windows junction and is not a selectable Target: {candidate}"
        )
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SelectionError(f"{label} does not exist: {candidate}") from exc
    if not resolved.is_file():
        if resolved.is_dir():
            raise SelectionError(
                f"{label} is not a regular file: {candidate}; a directory exists at that name, "
                + "so add a trailing '/' if the directory was intended"
            )
        raise SelectionError(f"{label} is not a regular file: {candidate}")
    root_resolved = root.resolve()
    try:
        relative = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise SelectionError(f"{label} resolves outside its Scope root: {resolved}") from exc
    if len(relative.parts) != 1:
        raise SelectionError(
            f"{label} must resolve to a direct child file of its Scope root: {resolved}"
        )
    return resolved, relative.as_posix()


def _scope_accepts_kind(target_kind: TargetKind, expected_kind: TargetEntryKind) -> bool:
    return target_kind == "both" or target_kind == expected_kind


def _resolve_target_entry(
    name: str,
    root: Path,
    *,
    target_kind: TargetKind,
    expected_kind: TargetEntryKind,
    label: str,
) -> tuple[Path, str, TargetEntryKind]:
    validate_target_name(name, label=label, target_kind=expected_kind)
    if not _scope_accepts_kind(target_kind, expected_kind):
        raise SelectionError(
            f"{label} requests a {expected_kind} Target, but this Scope uses target_kind = {target_kind!r}"
        )
    if expected_kind == "directory":
        path, source_root = _resolve_target_directory(name, root, label=label)
        return path, source_root, "directory"
    path, source_root = _resolve_target_file(name, root, label=label)
    return path, source_root, "file"


def _resolve_scope_root(scope: TargetRootSpec) -> Path:
    candidate = scope.root
    if not candidate.exists():
        raise SelectionError(f"{scope.label} root does not exist: {candidate}")
    if not candidate.is_dir():
        raise SelectionError(f"{scope.label} root is not a directory: {candidate}")
    return candidate.resolve(strict=True)


def _entry_is_eligible_target(entry: Path, target_kind: TargetKind) -> bool:
    if target_kind == "directory":
        return entry.is_dir()
    if target_kind == "file":
        return entry.is_file()
    return entry.is_dir() or entry.is_file()


def _empty_scope_message(scope: TargetRootSpec) -> str:
    noun = {
        "directory": "directories",
        "file": "files",
        "both": "files or directories",
    }[scope.target_kind]
    return f"{scope.label} contains no eligible direct child {noun}"


def _expand_scope(scope: TargetRootSpec) -> tuple[tuple[Path, str, TargetEntryKind], ...]:
    root = _resolve_scope_root(scope)
    targets: list[tuple[Path, str, TargetEntryKind]] = []
    try:
        entries = sorted(root.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise SelectionError(f"cannot enumerate {scope.label} root: {root}") from exc
    for entry in entries:
        if safe_is_link_like(entry):
            continue
        if entry.is_dir():
            source_kind: TargetEntryKind = "directory"
        elif entry.is_file():
            source_kind = "file"
        else:
            continue
        if not _entry_is_eligible_target(entry, scope.target_kind):
            continue
        if _target_is_ignored(
            entry.name, directory=source_kind == "directory", patterns=scope.ignore
        ):
            continue
        targets.append(
            _resolve_target_entry(
                entry.name,
                root,
                target_kind=scope.target_kind,
                expected_kind=source_kind,
                label=f"target from {scope.label}",
            )
        )
    if not targets:
        raise SelectionError(_empty_scope_message(scope))
    return tuple(targets)


def _selector_target_noun(scope: TargetRootSpec) -> str:
    return {
        "directory": "directory Targets",
        "file": "file Targets",
        "both": "Targets",
    }[scope.target_kind]


def resolve_target_expression(
    target: BoundTargetSpec,
) -> tuple[ResolvedTarget, ...]:
    """Resolve one bound Target expression against its filesystem root."""

    expression = target.expression
    scope = target.root
    label = target.label

    def from_scope(
        scope: TargetRootSpec,
        targets: tuple[tuple[Path, str, TargetEntryKind], ...],
    ) -> tuple[ResolvedTarget, ...]:
        return tuple(
            ResolvedTarget(
                path=path,
                source_root=source_root,
                archive_root=_archive_root(source_root, scope.archive_prefix),
                source_kind=source_kind,
                scope_name=scope.name,
                scope_description=scope.description,
            )
            for path, source_root, source_kind in targets
        )

    def one_from_scope(
        scope: TargetRootSpec,
        name: str,
        *,
        expected_kind: TargetEntryKind,
        ignored_where: str,
    ) -> tuple[ResolvedTarget, ...]:
        if _target_is_ignored(
            name,
            directory=expected_kind == "directory",
            patterns=scope.ignore,
        ):
            rendered = name + ("/" if expected_kind == "directory" else "")
            raise SelectionError(f"{label} is ignored by {ignored_where}.ignore: {rendered!r}")
        path, source_root, source_kind = _resolve_target_entry(
            name,
            _resolve_scope_root(scope),
            target_kind=scope.target_kind,
            expected_kind=expected_kind,
            label=label,
        )
        return (
            ResolvedTarget(
                path=path,
                source_root=source_root,
                archive_root=_archive_root(source_root, scope.archive_prefix),
                source_kind=source_kind,
                scope_name=scope.name,
                scope_description=scope.description,
            ),
        )

    ignored_where = target.ignore_where

    if isinstance(expression, TargetScopeExpr):
        return from_scope(scope, _expand_scope(scope))

    if isinstance(expression, TargetEntryExpr):
        return one_from_scope(
            scope,
            expression.item.name,
            expected_kind=expression.item.kind,
            ignored_where=ignored_where,
        )

    if isinstance(expression, TargetListExpr):
        root = _resolve_scope_root(scope)
        targets: list[tuple[Path, str, TargetEntryKind]] = []
        for item in expression.items:
            if _target_is_ignored(
                item.name,
                directory=item.kind == "directory",
                patterns=scope.ignore,
            ):
                raise SelectionError(f"{label} is ignored by {ignored_where}.ignore: {item.raw!r}")
            targets.append(
                _resolve_target_entry(
                    item.name,
                    root,
                    target_kind=scope.target_kind,
                    expected_kind=item.kind,
                    label=f"{label} list item",
                )
            )
        return from_scope(scope, tuple(targets))

    if isinstance(expression, TargetRegexExpr):
        eligible = _expand_scope(scope)
        matched = tuple(
            target
            for target in eligible
            if expression.pattern.fullmatch(target[1] + ("/" if target[2] == "directory" else ""))
            is not None
        )
        if not matched:
            raise SelectionError(
                f"{label} regular-expression selector matched no eligible "
                + f"{_selector_target_noun(scope)} in {scope.label}: "
                + repr(expression.pattern_text)
            )
        return from_scope(scope, matched)

    raise AssertionError(f"unknown normalized Target expression: {type(expression).__name__}")

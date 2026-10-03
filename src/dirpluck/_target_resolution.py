"""Target and Scope reference resolution for effective Configurations."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath

from ._builder_common import _is_link_like
from ._builder_models import _EffectiveConfiguration, _ScopeBinding
from ._config_models import TargetIgnorePattern
from ._regex import compile_regular_expression
from .errors import SelectionError


def _target_name_matches(name: str, *, directory: bool, pattern: TargetIgnorePattern) -> bool:
    # Ignore is intentionally broad when no trailing '/' is written: the
    # pattern excludes matching files and directories. A trailing '/' narrows
    # the exclusion to directories only.
    if pattern.directory and not directory:
        return False
    if pattern.match == "exact":
        return name == pattern.value
    if pattern.match == "prefix":
        return name.startswith(pattern.value)
    if pattern.match == "suffix":
        return name.endswith(pattern.value)
    if pattern.match == "contains":
        return pattern.value in name
    raise AssertionError(f"unknown Scope ignore match kind: {pattern.match}")


def _target_is_ignored(
    name: str,
    *,
    directory: bool,
    patterns: tuple[TargetIgnorePattern, ...],
) -> bool:
    return any(
        _target_name_matches(name, directory=directory, pattern=pattern) for pattern in patterns
    )


def _validate_target_name(name: str, *, label: str, target_kind: str = "directory") -> None:
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        noun = {
            "directory": "directory",
            "file": "file",
            "both": "filesystem entry",
        }.get(target_kind)
        if noun is None:
            raise AssertionError(f"unknown Scope target kind: {target_kind}")
        raise SelectionError(f"{label} must name one direct child {noun}: {name!r}")


def _resolve_target_directory(name: str, root: Path, *, label: str) -> tuple[Path, str]:
    _validate_target_name(name, label=label)
    candidate = root / name
    if _is_link_like(candidate):
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
    _validate_target_name(name, label=label, target_kind="file")
    candidate = root / name
    if _is_link_like(candidate):
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


def _scope_accepts_kind(target_kind: str, expected_kind: str) -> bool:
    if target_kind == "both":
        return expected_kind in {"file", "directory"}
    return target_kind == expected_kind


def _resolve_target_entry(
    name: str,
    root: Path,
    *,
    target_kind: str,
    expected_kind: str,
    label: str,
) -> tuple[Path, str, str]:
    if expected_kind not in {"file", "directory"}:
        raise AssertionError(f"unknown requested Target kind: {expected_kind}")
    _validate_target_name(name, label=label, target_kind=expected_kind)
    if not _scope_accepts_kind(target_kind, expected_kind):
        raise SelectionError(
            f"{label} requests a {expected_kind} Target, but this Scope uses target_kind = {target_kind!r}"
        )
    if expected_kind == "directory":
        path, source_root = _resolve_target_directory(name, root, label=label)
        return path, source_root, "directory"
    path, source_root = _resolve_target_file(name, root, label=label)
    return path, source_root, "file"


def scope_label(name: str | None) -> str:
    return "unnamed Scope" if name is None else f"Scope {name!r}"


def scope_root_path(binding: _ScopeBinding) -> Path:
    scope = binding.scope
    base = binding.layer.config.manifest.parent
    candidate = base if scope.name is None else Path(scope.path or "")
    if scope.name is not None and not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve(strict=False)


def _resolve_scope_root(binding: _ScopeBinding) -> Path:
    scope = binding.scope
    candidate = scope_root_path(binding)
    if not candidate.exists():
        raise SelectionError(f"{scope_label(scope.name)} root does not exist: {candidate}")
    if not candidate.is_dir():
        raise SelectionError(f"{scope_label(scope.name)} root is not a directory: {candidate}")
    return candidate.resolve(strict=True)


def _target_reference_is_absolute(reference: str) -> bool:
    pure = PurePosixPath(reference)
    windows = PureWindowsPath(reference)
    return pure.is_absolute() or windows.is_absolute() or bool(windows.drive)


def _entry_is_eligible_target(entry: Path, target_kind: str) -> bool:
    if target_kind == "directory":
        return entry.is_dir()
    if target_kind == "file":
        return entry.is_file()
    if target_kind == "both":
        return entry.is_dir() or entry.is_file()
    raise AssertionError(f"unknown Scope target kind: {target_kind}")


def _empty_scope_message(binding: _ScopeBinding) -> str:
    scope = binding.scope
    if scope.target_kind == "directory":
        noun = "directories"
    elif scope.target_kind == "file":
        noun = "files"
    elif scope.target_kind == "both":
        noun = "files or directories"
    else:
        raise AssertionError(f"unknown Scope target kind: {scope.target_kind}")
    return f"{scope_label(scope.name)} contains no eligible direct child {noun}"


def _expand_scope(binding: _ScopeBinding) -> tuple[tuple[Path, str, str], ...]:
    root = _resolve_scope_root(binding)
    scope = binding.scope
    targets: list[tuple[Path, str, str]] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name):
        if _is_link_like(entry):
            continue
        if entry.is_dir():
            source_kind = "directory"
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
                label=f"target from {scope_label(scope.name)}",
            )
        )
    if not targets:
        raise SelectionError(_empty_scope_message(binding))
    return tuple(targets)


def target_selector_binding(
    reference: str,
    effective: _EffectiveConfiguration,
) -> tuple[_ScopeBinding, str, str] | None:
    """Return the Scope and selector body for one explicit Target-selector reference.

    Only the reserved ``:[...]`` and ``:<...>`` forms are recognized. Other
    colons remain ordinary literal Target-name characters for compatibility.
    """

    if reference.startswith((":[", ":<")):
        return _require_scope(effective, None), reference[1:], "[scope]"

    # Scope names are Configuration data rather than path syntax. Match the
    # longest configured name first so names containing ':' remain usable.
    named = sorted(
        (name for name in effective.scopes if name is not None),
        key=len,
        reverse=True,
    )
    for scope_name in named:
        prefix = f"{scope_name}:"
        if not reference.startswith(prefix):
            continue
        selector = reference[len(prefix) :]
        if selector.startswith(("[", "<")):
            return _require_scope(effective, scope_name), selector, f"[scope.{scope_name}]"

    # The selector marker reserves this reference shape even when the named
    # Scope is unknown. This prevents a typo such as ``missing:<...>`` from
    # silently becoming a literal default-Scope Target name.
    marker_positions = [index for marker in (":[", ":<") if (index := reference.find(marker)) > 0]
    if marker_positions:
        marker_index = min(marker_positions)
        scope_name = reference[:marker_index]
        if "/" not in scope_name and "\\" not in scope_name:
            _validate_target_name(scope_name, label="Scope name")
            binding = _require_scope(effective, scope_name)
            return binding, reference[marker_index + 1 :], f"[scope.{scope_name}]"
    return None


def _selector_target_noun(binding: _ScopeBinding) -> str:
    target_kind = binding.scope.target_kind
    if target_kind == "directory":
        return "directory Targets"
    if target_kind == "file":
        return "file Targets"
    if target_kind == "both":
        return "Targets"
    raise AssertionError(f"unknown Scope target kind: {target_kind}")


def _parse_target_list_items(body: str, *, label: str) -> tuple[tuple[str, str], ...]:
    if not body:
        raise SelectionError(f"{label} Target list selector must not be empty")
    items: list[tuple[str, str]] = []
    current: list[str] = []
    index = 0
    while index < len(body):
        char = body[index]
        if char != "/":
            current.append(char)
            index += 1
            continue
        if not current:
            raise SelectionError(
                f"{label} Target list selector must not contain an empty Target name"
            )
        run = 1
        while index + run < len(body) and body[index + run] == "/":
            run += 1
        if run >= 3:
            raise SelectionError(
                f"{label} Target list selector must not contain three or more consecutive '/'"
            )
        name = "".join(current)
        current.clear()
        at_end = index + run == len(body)
        if run == 1:
            if at_end:
                items.append((name, "directory"))
            else:
                items.append((name, "file"))
        else:  # directory marker plus list separator
            if at_end:
                raise SelectionError(
                    f"{label} Target list selector must name another Target after a directory separator"
                )
            items.append((name, "directory"))
        index += run
    if current:
        items.append(("".join(current), "file"))
    if not items:
        raise SelectionError(f"{label} Target list selector must not be empty")
    return tuple(items)


def _resolve_target_list_selector(
    selector: str,
    binding: _ScopeBinding,
    *,
    label: str,
    ignored_where: str,
) -> tuple[tuple[Path, str, str], ...]:
    if not selector.endswith("]"):
        raise SelectionError(f"{label} Target list selector must end with ']': {selector!r}")
    body = selector[1:-1]
    items = _parse_target_list_items(body, label=label)

    root = _resolve_scope_root(binding)
    scope = binding.scope
    targets: list[tuple[Path, str, str]] = []
    for name, expected_kind in items:
        _validate_target_name(name, label=f"{label} list item", target_kind=expected_kind)
        if _target_is_ignored(
            name,
            directory=expected_kind == "directory",
            patterns=scope.ignore,
        ):
            rendered = name + ("/" if expected_kind == "directory" else "")
            raise SelectionError(f"{label} is ignored by {ignored_where}.ignore: {rendered!r}")
        targets.append(
            _resolve_target_entry(
                name,
                root,
                target_kind=scope.target_kind,
                expected_kind=expected_kind,
                label=f"{label} list item",
            )
        )
    return tuple(targets)


def _resolve_target_regex_selector(
    selector: str,
    binding: _ScopeBinding,
    *,
    label: str,
) -> tuple[tuple[Path, str, str], ...]:
    if not selector.endswith(">"):
        raise SelectionError(f"{label} regular-expression selector must end with '>': {selector!r}")
    pattern_text = selector[1:-1]
    pattern = compile_regular_expression(
        pattern_text,
        where=label,
        error_type=SelectionError,
        label="regular-expression selector",
    )

    eligible = _expand_scope(binding)
    matched = tuple(
        target
        for target in eligible
        if pattern.fullmatch(target[1] + ("/" if target[2] == "directory" else "")) is not None
    )
    if not matched:
        raise SelectionError(
            f"{label} regular-expression selector matched no eligible {_selector_target_noun(binding)} in "
            + f"{scope_label(binding.scope.name)}: {pattern_text!r}"
        )
    return matched


def _resolve_target_selector(
    selector: str,
    binding: _ScopeBinding,
    *,
    label: str,
    ignored_where: str,
) -> tuple[tuple[Path, str, str], ...]:
    if selector.startswith("["):
        return _resolve_target_list_selector(
            selector,
            binding,
            label=label,
            ignored_where=ignored_where,
        )
    if selector.startswith("<"):
        return _resolve_target_regex_selector(selector, binding, label=label)
    raise AssertionError(f"unknown Target selector syntax: {selector!r}")


def _require_scope(effective: _EffectiveConfiguration, name: str | None) -> _ScopeBinding:
    try:
        return effective.scopes[name]
    except KeyError as exc:
        if name is None:
            raise SelectionError("unnamed Scope is not defined") from exc
        raise SelectionError(f"Scope {name!r} is not defined") from exc


def resolve_target_reference(
    reference: str,
    effective: _EffectiveConfiguration,
    *,
    label: str,
) -> tuple[tuple[Path, str, str | None, str, str | None], ...]:
    if not reference:
        raise SelectionError(f"{label} must not be empty")

    def from_scope(
        binding: _ScopeBinding,
        targets: tuple[tuple[Path, str, str], ...],
    ) -> tuple[tuple[Path, str, str | None, str, str | None], ...]:
        scope = binding.scope
        return tuple(
            (path, source_root, scope.namespace, source_kind, scope.description)
            for path, source_root, source_kind in targets
        )

    def one_from_scope(
        binding: _ScopeBinding,
        name: str,
        *,
        expected_kind: str,
        ignored_where: str,
    ) -> tuple[tuple[Path, str, str | None, str, str | None], ...]:
        scope = binding.scope
        if _target_is_ignored(
            name,
            directory=expected_kind == "directory",
            patterns=scope.ignore,
        ):
            rendered = name + ("/" if expected_kind == "directory" else "")
            raise SelectionError(f"{label} is ignored by {ignored_where}.ignore: {rendered!r}")
        path, source_root, source_kind = _resolve_target_entry(
            name,
            _resolve_scope_root(binding),
            target_kind=scope.target_kind,
            expected_kind=expected_kind,
            label=label,
        )
        return ((path, source_root, scope.namespace, source_kind, scope.description),)

    selector_binding = target_selector_binding(reference, effective)
    if selector_binding is not None:
        binding, selector, ignored_where = selector_binding
        return from_scope(
            binding,
            _resolve_target_selector(
                selector,
                binding,
                label=label,
                ignored_where=ignored_where,
            ),
        )

    if "\\" in reference:
        raise SelectionError(f"{label} must use '/' as the separator: {reference!r}")

    if reference == "/":
        binding = _require_scope(effective, None)
        return from_scope(binding, _expand_scope(binding))

    if _target_reference_is_absolute(reference):
        raise SelectionError(
            f"{label} must use NAME, ./NAME, ./NAME/, SCOPE/NAME, SCOPE/NAME/, '/', SCOPE/, "
            + ":[...], :<...>, SCOPE:[...], or SCOPE:<...>: {reference!r}"
        )

    # ``./`` explicitly selects the unnamed Scope and avoids the intentional
    # ``SCOPE/`` expansion grammar for unnamed-Scope directory Targets.
    if reference.startswith("./"):
        body = reference[2:]
        expected_kind = "directory" if body.endswith("/") else "file"
        name = body[:-1] if expected_kind == "directory" else body
        _validate_target_name(name, label=label, target_kind=expected_kind)
        binding = _require_scope(effective, None)
        return one_from_scope(
            binding,
            name,
            expected_kind=expected_kind,
            ignored_where="[scope]",
        )

    if reference.endswith("/"):
        body = reference[:-1]
        parts = body.split("/")
        if len(parts) == 1:
            scope_name = parts[0]
            _validate_target_name(scope_name, label="Scope name")
            binding = _require_scope(effective, scope_name)
            return from_scope(binding, _expand_scope(binding))
        if len(parts) == 2 and all(parts):
            scope_name, name = parts
            _validate_target_name(scope_name, label="Scope name")
            _validate_target_name(name, label=label, target_kind="directory")
            binding = _require_scope(effective, scope_name)
            return one_from_scope(
                binding,
                name,
                expected_kind="directory",
                ignored_where=f"[scope.{scope_name}]",
            )
        raise SelectionError(f"{label} must name one direct-child directory Target: {reference!r}")

    parts = reference.split("/")
    if len(parts) == 1:
        name = parts[0]
        binding = _require_scope(effective, None)
        return one_from_scope(
            binding,
            name,
            expected_kind="file",
            ignored_where="[scope]",
        )

    if len(parts) == 2 and all(parts):
        scope_name, name = parts
        _validate_target_name(scope_name, label="Scope name")
        _validate_target_name(name, label=label, target_kind="file")
        binding = _require_scope(effective, scope_name)
        return one_from_scope(
            binding,
            name,
            expected_kind="file",
            ignored_where=f"[scope.{scope_name}]",
        )

    raise SelectionError(
        f"{label} must use NAME, ./NAME, ./NAME/, SCOPE/NAME, SCOPE/NAME/, '/', SCOPE/, "
        + ":[...], :<...>, SCOPE:[...], or SCOPE:<...>: {reference!r}"
    )

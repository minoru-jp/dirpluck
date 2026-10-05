"""Typed parsing for runtime Target reference syntax."""

from __future__ import annotations

from pathlib import PurePosixPath, PureWindowsPath
from collections.abc import Collection

from ._regex import compile_regular_expression
from .errors import SelectionError

from ._target_models import (
    ParsedTargetReference,
    TargetEntryExpr,
    TargetEntryKind,
    TargetItem,
    TargetListExpr,
    TargetRegexExpr,
    TargetScopeExpr,
    validate_target_name,
)


def _target_reference_is_absolute(reference: str) -> bool:
    pure = PurePosixPath(reference)
    windows = PureWindowsPath(reference)
    return pure.is_absolute() or windows.is_absolute() or bool(windows.drive)


def _parse_target_list_items(body: str, *, label: str) -> tuple[TargetItem, ...]:
    if not body:
        raise SelectionError(f"{label} Target list selector must not be empty")
    items: list[TargetItem] = []
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
            items.append(TargetItem(name=name, kind="directory" if at_end else "file"))
        else:  # directory marker plus list separator
            if at_end:
                raise SelectionError(
                    f"{label} Target list selector must name another Target after a directory separator"
                )
            items.append(TargetItem(name=name, kind="directory"))
        index += run
    if current:
        items.append(TargetItem(name="".join(current), kind="file"))
    if not items:
        raise SelectionError(f"{label} Target list selector must not be empty")
    for item in items:
        validate_target_name(item.name, label=f"{label} list item", target_kind=item.kind)
    return tuple(items)


def _parse_selector(
    selector: str,
    *,
    label: str,
) -> TargetListExpr | TargetRegexExpr:
    if selector.startswith("["):
        if not selector.endswith("]"):
            raise SelectionError(f"{label} Target list selector must end with ']': {selector!r}")
        return TargetListExpr(
            items=_parse_target_list_items(selector[1:-1], label=label),
        )
    if selector.startswith("<"):
        if not selector.endswith(">"):
            raise SelectionError(
                f"{label} regular-expression selector must end with '>': {selector!r}"
            )
        pattern_text = selector[1:-1]
        return TargetRegexExpr(
            pattern_text=pattern_text,
            pattern=compile_regular_expression(
                pattern_text,
                where=label,
                error_type=SelectionError,
                label="regular-expression selector",
            ),
        )
    raise AssertionError(f"unknown Target selector syntax: {selector!r}")


def _selector_parts(
    reference: str,
    *,
    scope_names: Collection[str | None],
) -> tuple[str | None, str] | None:
    if reference.startswith((":[", ":<")):
        return None, reference[1:]

    # Scope names are Configuration data rather than path syntax. Match the
    # longest configured name first so names containing ':' remain usable.
    named = sorted((name for name in scope_names if name is not None), key=len, reverse=True)
    for scope_name in named:
        prefix = f"{scope_name}:"
        if not reference.startswith(prefix):
            continue
        selector = reference[len(prefix) :]
        if selector.startswith(("[", "<")):
            return scope_name, selector

    # Reserve an explicit selector shape even when its named Scope is unknown,
    # so a misspelled Scope cannot silently become a literal default-Scope name.
    marker_positions = [index for marker in (":[", ":<") if (index := reference.find(marker)) > 0]
    if marker_positions:
        marker_index = min(marker_positions)
        scope_name = reference[:marker_index]
        if "/" not in scope_name and "\\" not in scope_name:
            validate_target_name(scope_name, label="Scope name")
            return scope_name, reference[marker_index + 1 :]
    return None


def parse_target_reference(
    reference: str,
    *,
    scope_names: Collection[str | None],
    label: str,
) -> ParsedTargetReference:
    """Parse one canonical Target reference without inspecting source filesystems."""

    if not reference:
        raise SelectionError(f"{label} must not be empty")

    selector_parts = _selector_parts(reference, scope_names=scope_names)
    if selector_parts is not None:
        scope, selector = selector_parts
        return ParsedTargetReference(
            scope=scope,
            expression=_parse_selector(selector, label=label),
        )

    if "\\" in reference:
        raise SelectionError(f"{label} must use '/' as the separator: {reference!r}")

    if reference == "/":
        return ParsedTargetReference(scope=None, expression=TargetScopeExpr())

    if _target_reference_is_absolute(reference):
        raise SelectionError(
            f"{label} must use NAME, ./NAME, ./NAME/, SCOPE/NAME, SCOPE/NAME/, '/', SCOPE/, "
            + f":[...], :<...>, SCOPE:[...], or SCOPE:<...>: {reference!r}"
        )

    # ``./`` explicitly selects the unnamed Scope and avoids the intentional
    # ``SCOPE/`` expansion grammar for unnamed-Scope directory Targets.
    if reference.startswith("./"):
        body = reference[2:]
        kind: TargetEntryKind = "directory" if body.endswith("/") else "file"
        name = body[:-1] if kind == "directory" else body
        validate_target_name(name, label=label, target_kind=kind)
        return ParsedTargetReference(
            scope=None,
            expression=TargetEntryExpr(item=TargetItem(name=name, kind=kind)),
        )

    if reference.endswith("/"):
        body = reference[:-1]
        parts = body.split("/")
        if len(parts) == 1:
            scope_name = parts[0]
            validate_target_name(scope_name, label="Scope name")
            return ParsedTargetReference(scope=scope_name, expression=TargetScopeExpr())
        if len(parts) == 2 and all(parts):
            scope_name, name = parts
            validate_target_name(scope_name, label="Scope name")
            validate_target_name(name, label=label, target_kind="directory")
            return ParsedTargetReference(
                scope=scope_name,
                expression=TargetEntryExpr(
                    item=TargetItem(name=name, kind="directory"),
                ),
            )
        raise SelectionError(f"{label} must name one direct-child directory Target: {reference!r}")

    parts = reference.split("/")
    if len(parts) == 1:
        name = parts[0]
        validate_target_name(name, label=label, target_kind="file")
        return ParsedTargetReference(
            scope=None,
            expression=TargetEntryExpr(item=TargetItem(name=name, kind="file")),
        )

    if len(parts) == 2 and all(parts):
        scope_name, name = parts
        validate_target_name(scope_name, label="Scope name")
        validate_target_name(name, label=label, target_kind="file")
        return ParsedTargetReference(
            scope=scope_name,
            expression=TargetEntryExpr(item=TargetItem(name=name, kind="file")),
        )

    raise SelectionError(
        f"{label} must use NAME, ./NAME, ./NAME/, SCOPE/NAME, SCOPE/NAME/, '/', SCOPE/, "
        + f":[...], :<...>, SCOPE:[...], or SCOPE:<...>: {reference!r}"
    )

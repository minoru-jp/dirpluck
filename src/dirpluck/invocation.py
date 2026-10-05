"""Strict parsing and CLI selection for dirpluck Invocation Template documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from collections.abc import Mapping
import tomllib
from typing import cast

from ._archive_mtime import validate_archive_mtime_spec
from ._case import CaseSelection, parse_case_selection
from ._input_paths import (
    CONFIG_SUFFIX,
    lexical_absolute_path,
    validate_filesystem_location,
)
from .errors import ConfigurationError, InvocationError

INVOCATION_SUFFIX = ".dirpluck-inv"
_INVOCATION_FIELDS = {"config", "targets", "case", "archive_mtime"}


def _invocation_reference(reference: str) -> str:
    """Normalize one CLI Invocation Template reference to a concrete document path."""

    if not isinstance(reference, str) or not reference.strip():
        raise InvocationError("invocation template path must be a non-empty string")
    raw = reference.strip()
    if raw.endswith("/") or raw.rsplit("/", 1)[-1] in {".", ".."}:
        raise InvocationError("invocation template path must name one Invocation Template file")
    try:
        path = validate_filesystem_location(
            raw,
            "--invocation-template",
            label="Invocation Template path",
        )
    except ConfigurationError as exc:
        raise InvocationError(str(exc)) from exc
    if not path.endswith(INVOCATION_SUFFIX):
        path += INVOCATION_SUFFIX
    return path


def resolve_invocation_path(reference: str, *, cwd: Path | None = None) -> Path:
    """Resolve one explicitly supplied Invocation Template document path."""

    normalized = _invocation_reference(reference)
    candidate = lexical_absolute_path(normalized, cwd=cwd)
    if not candidate.is_file():
        raise InvocationError(f"invocation template file was not found: {candidate}")
    return candidate


@dataclass(frozen=True)
class Invocation:
    """One default or named reusable CLI invocation in a .dirpluck-inv document."""

    manifest: Path
    config: str | None
    targets: tuple[str, ...]
    case: CaseSelection | None
    archive_mtime: str | None

    def config_path(self) -> Path | None:
        """Resolve the optional Configuration reference relative to this document."""

        if self.config is None:
            return None
        return lexical_absolute_path(self.config, cwd=self.manifest.parent)

    @property
    def is_empty(self) -> bool:
        """Whether this Invocation contributes no stored runtime inputs."""

        return (
            self.config is None
            and not self.targets
            and self.case is None
            and self.archive_mtime is None
        )


@dataclass(frozen=True)
class InvocationTemplate:
    """One .dirpluck-inv document containing default and named Invocations."""

    manifest: Path
    default: Invocation
    entries: Mapping[str, Invocation]

    def select(self, name: str | None = None) -> Invocation:
        """Select the default Invocation or one named entry."""

        if name is None:
            return self.default
        if not isinstance(name, str) or not name.strip():
            raise InvocationError("invocation entry name must be a non-empty string")
        try:
            return self.entries[name]
        except KeyError as exc:
            raise InvocationError(f"invocation entry was not found: {name}") from exc


def _require_only_keys(table: Mapping[str, object], allowed: set[str], where: str) -> None:
    unknown = sorted(set(table) - allowed)
    if unknown:
        raise InvocationError(f"{where}: unknown key(s): {', '.join(unknown)}")


def _parse_optional_config(value: object, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvocationError(f"{where}: expected a string")
    if value.endswith("/"):
        raise InvocationError(f"{where}: config must name one Configuration file")
    try:
        path = validate_filesystem_location(
            value,
            where,
            label="Configuration path",
        )
    except ConfigurationError as exc:
        raise InvocationError(str(exc)) from exc
    if not path.endswith(CONFIG_SUFFIX):
        path += CONFIG_SUFFIX
    return path


def _parse_targets(value: object, where: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise InvocationError(f"{where}: expected an array")
    items = cast(list[object], value)
    targets: list[str] = []
    for index, item in enumerate(items):
        item_where = f"{where}[{index}]"
        if not isinstance(item, str) or not item:
            raise InvocationError(f"{item_where}: expected a non-empty string")
        targets.append(item)
    return tuple(targets)


def _parse_optional_case(value: object, where: str) -> CaseSelection | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise InvocationError(f"{where}: expected a non-empty string")
    try:
        return parse_case_selection(value)
    except ValueError as exc:
        raise InvocationError(f"{where}: {exc}") from exc


def _parse_optional_archive_mtime(value: object, where: str) -> str | None:
    if value is None:
        return None
    try:
        return validate_archive_mtime_spec(value)
    except ValueError as exc:
        raise InvocationError(f"{where}: {exc}") from exc


def _parse_invocation(
    table: Mapping[str, object],
    *,
    manifest: Path,
    where: str,
) -> Invocation:
    _require_only_keys(table, _INVOCATION_FIELDS, where)
    return Invocation(
        manifest=manifest,
        config=_parse_optional_config(table.get("config"), f"{where}.config"),
        targets=_parse_targets(table.get("targets"), f"{where}.targets"),
        case=_parse_optional_case(table.get("case"), f"{where}.case"),
        archive_mtime=_parse_optional_archive_mtime(
            table.get("archive_mtime"),
            f"{where}.archive_mtime",
        ),
    )


def load_invocation(path: str | Path) -> InvocationTemplate:
    """Load one Invocation Template document."""

    manifest = lexical_absolute_path(Path(path).expanduser())
    if manifest.suffix != INVOCATION_SUFFIX:
        raise InvocationError(
            f"invocation template file must end with {INVOCATION_SUFFIX!r}: {manifest}"
        )
    try:
        with manifest.open("rb") as file:
            raw_data = tomllib.load(file)
    except FileNotFoundError as exc:
        raise InvocationError(f"invocation template file was not found: {manifest}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise InvocationError(f"invalid TOML in {manifest}: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise InvocationError(f"{manifest}: top level must be a table")
    data = cast(dict[str, object], raw_data)
    _require_only_keys(data, {"invocation"}, str(manifest))

    if "invocation" not in data:
        raise InvocationError(f"{manifest}: [invocation] table is required")
    raw_invocation = data["invocation"]
    where = f"{manifest} [invocation]"
    if not isinstance(raw_invocation, dict):
        raise InvocationError(f"{where}: expected a table")
    invocation_table = cast(dict[str, object], raw_invocation)

    for field in sorted(_INVOCATION_FIELDS):
        if isinstance(invocation_table.get(field), dict):
            raise InvocationError(
                f"{where}: invocation entry name {field!r} is reserved for the [invocation].{field} field"
            )

    root_fields = {
        key: value for key, value in invocation_table.items() if key in _INVOCATION_FIELDS
    }
    default = _parse_invocation(root_fields, manifest=manifest, where=where)

    entries: dict[str, Invocation] = {}
    unknown_keys: list[str] = []
    for key, value in invocation_table.items():
        if key in _INVOCATION_FIELDS:
            continue
        if not isinstance(value, dict):
            unknown_keys.append(key)
            continue
        entries[key] = _parse_invocation(
            cast(dict[str, object], value),
            manifest=manifest,
            where=f"{manifest} [invocation.{key}]",
        )
    if unknown_keys:
        raise InvocationError(f"{where}: unknown key(s): {', '.join(sorted(unknown_keys))}")

    return InvocationTemplate(
        manifest=manifest,
        default=default,
        entries=MappingProxyType(entries),
    )

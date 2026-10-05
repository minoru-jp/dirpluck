"""Selection normalization performed during Configuration compilation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from ._config_models import SelectionDefinition, SharedPatterns, SharedReference
from ._selection_models import (
    ExclusionPattern,
    IncludePattern,
    MatchPattern,
    PathExclusion,
    Selection,
)
from ._selection_validation import (
    reject_duplicate_exclusions,
    reject_duplicate_selection_entries,
    render_selection_entry,
    selection_entry_key,
)
from .errors import ConfigurationError

IncludeEntry = IncludePattern | MatchPattern
IgnoreEntry = ExclusionPattern | PathExclusion | MatchPattern
Pattern = IncludeEntry | IgnoreEntry


def _expand(
    items: tuple[Pattern | SharedReference, ...],
    namespace: Mapping[str, tuple[Pattern, ...]],
    where: str,
) -> tuple[Pattern, ...]:
    expanded: list[Pattern] = []
    for item in items:
        if not isinstance(item, SharedReference):
            expanded.append(item)
            continue
        try:
            expanded.extend(namespace[item.name])
        except KeyError as exc:
            raise ConfigurationError(f"{where}: unknown Shared pattern set: {item.name!r}") from exc
    return tuple(expanded)


def normalize_selection(
    selection: SelectionDefinition,
    shared: SharedPatterns,
    where: str,
) -> Selection:
    """Expand Shared references and validate one effective Selection."""

    must = cast(
        tuple[IncludeEntry, ...],
        _expand(
            cast(tuple[Pattern | SharedReference, ...], selection.must),
            cast(Mapping[str, tuple[Pattern, ...]], shared.must),
            f"{where}.must",
        ),
    )
    may = cast(
        tuple[IncludeEntry, ...],
        _expand(
            cast(tuple[Pattern | SharedReference, ...], selection.may),
            cast(Mapping[str, tuple[Pattern, ...]], shared.may),
            f"{where}.may",
        ),
    )
    ignore = cast(
        tuple[IgnoreEntry, ...],
        _expand(
            cast(tuple[Pattern | SharedReference, ...], selection.ignore),
            cast(Mapping[str, tuple[Pattern, ...]], shared.ignore),
            f"{where}.ignore",
        ),
    )

    reject_duplicate_selection_entries(must, f"{where}.must")
    reject_duplicate_selection_entries(may, f"{where}.may")
    must_by_key = {selection_entry_key(item): item for item in must}
    overlap = [
        must_by_key[key]
        for key in sorted(set(must_by_key) & {selection_entry_key(item) for item in may})
    ]
    if overlap:
        raise ConfigurationError(
            f"{where}: must and may must not contain the same pattern(s): "
            + ", ".join(render_selection_entry(item) for item in overlap)
        )
    reject_duplicate_exclusions(ignore, f"{where}.ignore")
    if selection.allow_empty and must:
        raise ConfigurationError(
            f"{where}.allow_empty: true cannot be used when effective must patterns exist"
        )
    return Selection(
        description=selection.description,
        must=must,
        may=may,
        ignore=ignore,
        allow_empty=selection.allow_empty,
    )

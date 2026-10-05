"""Runtime Case selector parsing shared by CLI, API, and Invocation Templates."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CaseSelection:
    """Independent Pluck and Always Case names selected for one run."""

    pluck: str | None = None
    always: str | None = None


def parse_case_selection(value: str | None) -> CaseSelection:
    """Parse ``PLUCK``, ``.ALWAYS``, or ``PLUCK.ALWAYS`` Case syntax."""

    if value is None:
        return CaseSelection()
    if not isinstance(value, str) or not value.strip():
        raise ValueError("case must be a non-empty string")

    dot_count = value.count(".")
    if dot_count == 0:
        return CaseSelection(pluck=value)
    if dot_count != 1:
        raise ValueError("case must use PLUCK, .ALWAYS, or PLUCK.ALWAYS syntax")

    pluck, always = value.split(".", 1)
    if not always:
        raise ValueError("case must use PLUCK, .ALWAYS, or PLUCK.ALWAYS syntax")
    if not always.strip() or (pluck and not pluck.strip()):
        raise ValueError("case names must be non-empty")
    return CaseSelection(pluck=pluck or None, always=always)

"""Shared regular-expression validation helpers."""

from __future__ import annotations

import re
from typing import TypeVar


REGEX_MAX_LENGTH = 512

_Error = TypeVar("_Error", bound=Exception)


def compile_regular_expression(
    text: str,
    *,
    where: str,
    error_type: type[_Error],
    label: str,
) -> re.Pattern[str]:
    """Validate and compile one bounded Python-compatible regular expression."""

    if not text:
        raise error_type(f"{where}: {label} must not be empty")
    if len(text) > REGEX_MAX_LENGTH:
        raise error_type(f"{where}: {label} exceeds the {REGEX_MAX_LENGTH}-character limit")
    try:
        return re.compile(text)
    except re.error as exc:
        raise error_type(f"{where}: invalid {label} {text!r}: {exc}") from exc

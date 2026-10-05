"""Warning categories and delivery helpers exposed by dirpluck."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
import inspect
from typing import cast
import warnings


class ConfigurationDeprecationWarning(FutureWarning):
    """Warn that deprecated Configuration syntax will become invalid."""


class AlwaysMigrationWarning(FutureWarning):
    """Warn about pre-1.0 Always migration behavior that requires attention."""


_WARNING_COLLECTION: ContextVar[list[tuple[type[Warning], str]] | None] = ContextVar(
    "dirpluck_warning_collection",
    default=None,
)


@contextmanager
def collect_dirpluck_warnings() -> Generator[list[tuple[type[Warning], str]], None, None]:
    """Collect public migration warnings for one caller instead of emitting them."""

    collected: list[tuple[type[Warning], str]] = []
    token = _WARNING_COLLECTION.set(collected)
    try:
        yield collected
    finally:
        _WARNING_COLLECTION.reset(token)


def report_dirpluck_warning(message: str, category: type[Warning]) -> None:
    """Report one public warning, attributing API use to the external caller."""

    collected = _WARNING_COLLECTION.get()
    if collected is not None:
        item = (category, message)
        if item not in collected:
            collected.append(item)
        return

    # Attribute API warnings to the first caller outside dirpluck rather than
    # to an internal parser/effective-resolution frame. Different code paths
    # have different depths, so a fixed stacklevel is not a stable API contract.
    stacklevel = 1
    frame = inspect.currentframe()
    try:
        while frame is not None:
            module_name = cast(str, frame.f_globals.get("__name__", ""))
            if module_name != "dirpluck" and not module_name.startswith("dirpluck."):
                break
            stacklevel += 1
            frame = frame.f_back
    finally:
        del frame

    warnings.warn(message, category, stacklevel=stacklevel)

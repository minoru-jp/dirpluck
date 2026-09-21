"""Common builder helpers shared across pipeline stages."""

from pathlib import Path

from ._filesystem import LinkInspectionError, is_link_like
from .errors import SelectionError


def _is_link_like(path: Path) -> bool:
    """Return whether one filesystem entry must not be followed by dirpluck."""

    try:
        return is_link_like(path)
    except LinkInspectionError as exc:
        raise SelectionError(str(exc)) from exc

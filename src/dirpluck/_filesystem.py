"""Low-level filesystem classification shared across dirpluck."""

from __future__ import annotations

from pathlib import Path
import os
import stat
from typing import cast

from .errors import SelectionError


class LinkInspectionError(OSError):
    """Raised when link-like filesystem semantics cannot be inspected safely."""


def is_link_like(path: Path) -> bool:
    """Return whether *path* is a symbolic link or Windows directory junction."""

    if path.is_symlink():
        return True
    if os.name != "nt":
        return False

    junction_tag = cast(int | None, getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", None))
    if not isinstance(junction_tag, int):
        raise LinkInspectionError(
            "cannot safely inspect Windows junctions: "
            + "stat.IO_REPARSE_TAG_MOUNT_POINT is unavailable"
        )
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise LinkInspectionError(f"cannot inspect filesystem entry: {path}") from exc

    reparse_tag = cast(int | None, getattr(info, "st_reparse_tag", None))
    if reparse_tag is None:
        raise LinkInspectionError(
            f"cannot safely inspect Windows junctions: st_reparse_tag is unavailable for {path}"
        )
    return reparse_tag == junction_tag


def safe_is_link_like(path: Path) -> bool:
    """Return link-like status, failing closed with a dirpluck SelectionError."""

    try:
        return is_link_like(path)
    except LinkInspectionError as exc:
        raise SelectionError(str(exc)) from exc

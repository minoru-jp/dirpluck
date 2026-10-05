"""ZIP-writer input produced after archive rendering."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArchivePayload:
    """Only the archive content required by the ZIP writer."""

    entries: Mapping[str, Path]
    readme: str
    empty_directories: tuple[str, ...] = ()

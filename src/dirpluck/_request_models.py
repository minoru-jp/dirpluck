"""Runtime request models accepted by input normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ._case import CaseSelection, parse_case_selection


@dataclass(frozen=True)
class RuntimeOutput:
    """One runtime-selected exact output path or generated-name directory."""

    path: Path
    generated: bool


@dataclass(frozen=True)
class BuildRequest:
    """One build request with Target references and runtime archive options."""

    targets: tuple[str, ...] = ()
    case: CaseSelection = CaseSelection()
    sequence: int | None = None
    paths: bool = False
    archive_mtime: datetime | None = None
    output: RuntimeOutput | None = None
    force: bool = False

    @classmethod
    def create(
        cls,
        *targets: str | Path,
        case: str | CaseSelection | None = None,
        sequence: int | None = None,
        paths: bool = False,
        archive_mtime: datetime | None = None,
        output: RuntimeOutput | None = None,
        force: bool = False,
    ) -> "BuildRequest":
        return cls(
            targets=tuple(
                target.as_posix() if isinstance(target, Path) else str(target) for target in targets
            ),
            case=case if isinstance(case, CaseSelection) else parse_case_selection(case),
            sequence=sequence,
            paths=paths,
            archive_mtime=archive_mtime,
            output=output,
            force=force,
        )

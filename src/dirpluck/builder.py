"""Internal archive build orchestration."""

from __future__ import annotations

from pathlib import Path

from ._archive import plan_archive
from ._builder_models import ArchivePlan, BuildRequest
from ._output import _prepare_output, _write_archive
from .config import Config


def _build_archive_with_plan(
    config: Config,
    request: BuildRequest,
) -> tuple[Path, ArchivePlan]:
    """Build one ZIP archive and return the path together with the exact plan used."""

    output_path, overwrite = _prepare_output(config, request)
    plan = plan_archive(config, request)
    return (
        _write_archive(
            plan,
            output_path,
            overwrite,
            archive_mtime=request.archive_mtime,
        ),
        plan,
    )


def build_archive(
    config: Config,
    request: BuildRequest,
) -> Path:
    """Build one ZIP archive using the Output policy declared by the root Configuration."""

    path, _ = _build_archive_with_plan(config, request)
    return path

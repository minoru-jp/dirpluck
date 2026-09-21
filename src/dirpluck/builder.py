"""Internal archive build orchestration."""

from __future__ import annotations

from pathlib import Path

from . import _archive, _builder_models, _output
from . import config as _config


def _build_archive_with_plan(
    config: _config.Config,
    request: _builder_models.BuildRequest,
) -> tuple[Path, _builder_models.ArchivePlan]:
    """Build one ZIP archive and return the path together with the exact plan used."""

    output_path, overwrite = _output._prepare_output(config, request)
    plan = _archive.plan_archive(config, request)
    return (
        _output._write_archive(
            plan,
            output_path,
            overwrite,
            archive_mtime=request.archive_mtime,
        ),
        plan,
    )


def build_archive(
    config: _config.Config,
    request: _builder_models.BuildRequest,
) -> Path:
    """Build one ZIP archive using the Output policy declared by the root Configuration."""

    path, _ = _build_archive_with_plan(config, request)
    return path

"""Internal archive build orchestration."""

from __future__ import annotations

from pathlib import Path

from ._archive import create_archive_plan
from ._archive_models import ArchivePlan
from ._request_models import BuildRequest
from ._extraction import extract
from ._normalization import NormalizedExecution, normalize
from ._output import prepare_output, write_archive
from ._compatibility import report_compatibility_notices
from ._config_models import Config
from .errors import ConfigurationError


def _prepare_archive(
    config: Config,
    request: BuildRequest,
    *,
    allow_missing: bool = False,
) -> tuple[NormalizedExecution, ArchivePlan]:
    """Normalize, extract, and render one archive without touching Output."""

    execution = normalize(config, request)
    report_compatibility_notices(execution.compatibility_notices)
    extraction = extract(execution.extraction, allow_missing=allow_missing)
    return execution, create_archive_plan(extraction, execution.presentation)


def build_archive_with_plan(
    config: Config,
    request: BuildRequest,
) -> tuple[Path, ArchivePlan]:
    """Prepare and write one ZIP archive."""

    execution, plan = _prepare_archive(config, request)
    output = execution.output
    if output is None:
        raise ConfigurationError(
            f"{config.manifest}: the root Configuration must define "
            + "[output] or [output.timestamp], or the invocation must provide runtime output"
        )
    output_path, overwrite = prepare_output(output)
    return (
        write_archive(
            plan.payload,
            output_path,
            overwrite,
            archive_mtime=output.archive_mtime,
        ),
        plan,
    )


def plan_archive(
    config: Config,
    request: BuildRequest,
    *,
    allow_missing: bool = False,
) -> ArchivePlan:
    """Normalize, extract, and render one archive plan without writing a ZIP."""

    _, plan = _prepare_archive(config, request, allow_missing=allow_missing)
    return plan

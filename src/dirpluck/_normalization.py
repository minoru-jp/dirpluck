"""Input normalization for Configuration and runtime invocation semantics."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from ._extraction_spec import ExtractionSpec
from ._output_models import ArchivePresentation, NormalizedOutput
from ._request_models import BuildRequest
from ._compatibility import CompatibilityNotice
from ._config_models import Config
from ._configuration_compiler import compile_collection_input
from .errors import SelectionError


@dataclass(frozen=True)
class NormalizedExecution:
    """One normalized invocation split into extraction and output concerns."""

    extraction: ExtractionSpec
    output: NormalizedOutput | None
    presentation: ArchivePresentation
    compatibility_notices: tuple[CompatibilityNotice, ...] = ()


def _normalized_output(config: Config, request: BuildRequest) -> NormalizedOutput | None:
    configured = config.output
    runtime = request.output

    if runtime is not None:
        path = runtime.path
        generated = runtime.generated
        overwrite = request.force
        if generated and configured is not None and configured.generated:
            prefix = configured.prefix
            suffix = configured.suffix
        elif generated:
            prefix = "dirpluck"
            suffix = None
        else:
            prefix = None
            suffix = None
    elif configured is not None:
        candidate = Path(configured.path)
        if not candidate.is_absolute():
            candidate = config.manifest.parent / candidate
        path = Path(os.path.abspath(candidate))
        generated = configured.generated
        overwrite = request.force or (configured.overwrite if not generated else False)
        prefix = configured.prefix if generated else None
        suffix = configured.suffix if generated else None
    else:
        path = None
        generated = False
        overwrite = request.force
        prefix = None
        suffix = None

    if request.sequence is not None:
        if (
            isinstance(request.sequence, bool)
            or not isinstance(request.sequence, int)
            or request.sequence < 1
        ):
            raise SelectionError("output sequence must be an integer greater than or equal to 1")
        if not generated:
            raise SelectionError("output sequence can only be used with timestamp output")
    if not isinstance(request.force, bool):
        raise SelectionError("output force must be a boolean")
    if path is None:
        return None

    return NormalizedOutput(
        path=path,
        generated=generated,
        overwrite=overwrite,
        prefix=prefix,
        suffix=suffix,
        sequence=request.sequence,
        archive_mtime=request.archive_mtime,
    )


def normalize(config: Config, request: BuildRequest) -> NormalizedExecution:
    """Compile all non-filesystem input semantics for one execution."""

    extraction, collection_presentation, compatibility_notices = compile_collection_input(
        config,
        case=request.case,
        target_references=request.targets,
    )
    return NormalizedExecution(
        extraction=extraction,
        output=_normalized_output(config, request),
        presentation=ArchivePresentation(
            about_description=collection_presentation.about_description,
            description_no_targets=collection_presentation.description_no_targets,
            description_no_always=collection_presentation.description_no_always,
            description_empty=collection_presentation.description_empty,
            layout_descriptions=collection_presentation.layout_descriptions,
            show_source_paths=request.paths,
        ),
        compatibility_notices=compatibility_notices,
    )

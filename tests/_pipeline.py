"""Test-only adapters for exercising internal pipeline boundaries."""

from __future__ import annotations

from pathlib import Path

from dirpluck._compatibility import report_compatibility_notices
from dirpluck._config_models import Config
from dirpluck._normalization import normalize
from dirpluck._request_models import BuildRequest
from dirpluck._resolution_models import ResolvedSource
from dirpluck._source_resolution import resolve_normalized_sources
from dirpluck.builder import build_archive_with_plan


def resolve_sources(config: Config, request: BuildRequest) -> tuple[ResolvedSource, ...]:
    """Normalize and resolve sources without collecting files."""

    execution = normalize(config, request)
    report_compatibility_notices(execution.compatibility_notices)
    return resolve_normalized_sources(execution.extraction)


def build_archive(config: Config, request: BuildRequest) -> Path:
    """Run the production build pipeline and return only its output path."""

    path, _ = build_archive_with_plan(config, request)
    return path

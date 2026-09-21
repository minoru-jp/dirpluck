"""High-level application layer shared by the Python API and CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from ._archive import plan_archive, render_archive_tree
from ._archive_mtime import resolve_archive_mtime, validate_archive_mtime_spec
from ._builder_models import BuildRequest
from .builder import _build_archive_with_plan
from .config import load_config, resolve_config_path
from .errors import UsageError
from .invocation import load_invocation, resolve_invocation_path


@dataclass(frozen=True)
class RunResult:
    """Result of one high-level dirpluck invocation."""

    output_path: Path | None
    preview_text: str
    archive_entries: tuple[str, ...]
    archive_readme: str
    skipped_link_count: int
    invocation_empty: bool = False


def _runtime_cwd(cwd: str | Path | None) -> Path:
    """Return one lexical absolute runtime cwd without resolving aliases."""

    if cwd is None:
        return Path.cwd()
    candidate = Path(cwd).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    return Path(os.path.abspath(candidate))


def _validate_run_arguments(
    targets: tuple[str | Path, ...],
    *,
    config: str | None,
    sequence: int | None,
    invocation: str | None,
    entry: str | None,
    preview: bool,
    archive_mtime: str | None,
) -> None:
    if preview and sequence is not None:
        raise UsageError("sequence cannot be combined with preview")
    if entry is not None and invocation is None:
        raise UsageError("entry requires invocation")
    if invocation is not None and config is not None:
        raise UsageError("config cannot be combined with invocation")
    if invocation is not None and targets:
        raise UsageError("targets cannot be combined with invocation")
    if sequence is not None and (isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1):
        raise UsageError("sequence must be an integer greater than or equal to 1")
    if archive_mtime is not None:
        try:
            validate_archive_mtime_spec(archive_mtime)
        except ValueError as exc:
            raise UsageError(str(exc)) from exc


def _archive_entry_names(plan) -> tuple[str, ...]:
    entries = {"README.md", *plan.entries.keys()}
    entries.update(f"{path.rstrip('/')}/" for path in plan.empty_directories)
    return ("README.md", *tuple(sorted(entries - {"README.md"})))


def run(
    *targets: str | Path,
    config: str | None = None,
    case: str | None = None,
    sequence: int | None = None,
    invocation: str | None = None,
    entry: str | None = None,
    preview: bool = False,
    paths: bool = False,
    archive_mtime: str | None = None,
    cwd: str | Path | None = None,
) -> RunResult:
    """Run dirpluck with the same high-level inputs exposed by the CLI.

    Relative ``config`` and ``invocation`` paths use ``cwd``.  When ``cwd`` is
    omitted, the process current working directory is used.  ``preview=True``
    performs archive planning without writing the ZIP.
    """

    _validate_run_arguments(
        targets,
        config=config,
        sequence=sequence,
        invocation=invocation,
        entry=entry,
        preview=preview,
        archive_mtime=archive_mtime,
    )
    runtime_cwd = _runtime_cwd(cwd)

    invocation_empty = False
    if invocation is None:
        config_path = resolve_config_path(config, cwd=runtime_cwd)
        directories = targets
        selected_case = case
        selected_archive_mtime = archive_mtime
    else:
        invocation_path = resolve_invocation_path(invocation, cwd=runtime_cwd)
        template = load_invocation(invocation_path)
        selected = template.select(entry)
        invocation_empty = selected.is_empty
        template_config = selected.config_path()
        config_path = (
            template_config
            if template_config is not None
            else resolve_config_path(cwd=runtime_cwd)
        )
        directories = selected.targets
        selected_case = case if case is not None else selected.case
        selected_archive_mtime = (
            archive_mtime if archive_mtime is not None else selected.archive_mtime
        )

    loaded = load_config(config_path)
    request = BuildRequest.create(
        *directories,
        case=selected_case,
        sequence=sequence,
        paths=paths,
        archive_mtime=resolve_archive_mtime(selected_archive_mtime),
    )

    if preview:
        plan = plan_archive(loaded, request, allow_missing=True)
        output_path = None
    else:
        output_path, plan = _build_archive_with_plan(loaded, request)

    return RunResult(
        output_path=output_path,
        preview_text=render_archive_tree(plan),
        archive_entries=_archive_entry_names(plan),
        archive_readme=plan.readme,
        skipped_link_count=plan.skipped_link_count,
        invocation_empty=invocation_empty,
    )

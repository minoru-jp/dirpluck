"""High-level application layer shared by the Python API and CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
import glob
import os

from ._archive import plan_archive, render_archive_tree
from ._archive_mtime import resolve_archive_mtime, validate_archive_mtime_spec
from ._builder_models import BuildRequest, RuntimeOutput
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


def _resolve_runtime_output(value: str | None, *, cwd: Path) -> RuntimeOutput | None:
    """Validate one runtime Output reference and anchor it to the runtime cwd."""

    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise UsageError("output path must be a non-empty string")
    if "\\" in value:
        raise UsageError(
            "output path: backslashes are not allowed in filesystem locations; "
            "use '/' as the path separator"
        )
    if glob.has_magic(value):
        raise UsageError("output path must name one concrete path")

    generated = value.endswith("/")
    pure = PurePosixPath(value)
    windows = PureWindowsPath(value)
    host = Path(value)
    has_non_host_root = (
        (pure.is_absolute() or bool(windows.drive) or bool(windows.root))
        and not host.is_absolute()
    )
    if has_non_host_root:
        raise UsageError(
            "output path: absolute-root form is not supported by the host operating system"
        )

    normalized = pure.as_posix()
    if not generated:
        final_component = value.rsplit("/", 1)[-1]
        if final_component in {"", ".", ".."} or pure == PurePosixPath("."):
            raise UsageError("output path must name a file or end with '/' for a directory")

    candidate = Path(normalized)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    return RuntimeOutput(path=Path(os.path.abspath(candidate)), generated=generated)

def _validate_run_arguments(
    targets: tuple[str | Path, ...],
    *,
    config: str | None,
    sequence: int | None,
    invocation: str | None,
    entry: str | None,
    preview: bool,
    archive_mtime: str | None,
    output: str | None,
    force: bool,
) -> None:
    if preview and sequence is not None:
        raise UsageError("sequence cannot be combined with preview")
    if preview and output is not None:
        raise UsageError("output cannot be combined with preview")
    if preview and force:
        raise UsageError("force cannot be combined with preview")
    if entry is not None and invocation is None:
        raise UsageError("entry requires invocation")
    if invocation is not None and config is not None:
        raise UsageError("config cannot be combined with invocation")
    if invocation is not None and targets:
        raise UsageError("targets cannot be combined with invocation")
    if sequence is not None and (
        isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1
    ):
        raise UsageError("sequence must be an integer greater than or equal to 1")
    if archive_mtime is not None:
        try:
            validate_archive_mtime_spec(archive_mtime)
        except ValueError as exc:
            raise UsageError(str(exc)) from exc
    if output is not None and (not isinstance(output, str) or not output):
        raise UsageError("output path must be a non-empty string")
    if not isinstance(force, bool):
        raise UsageError("force must be a boolean")


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
    output: str | None = None,
    force: bool = False,
    cwd: str | Path | None = None,
) -> RunResult:
    """Run dirpluck with the same high-level inputs exposed by the CLI.

    Relative ``config``, ``invocation``, and runtime ``output`` paths use
    ``cwd``.  When ``cwd`` is omitted, the process current working directory is
    used.  A runtime ``output`` ending in ``/`` selects automatic timestamp
    naming in that directory.  ``preview=True`` performs archive planning
    without writing the ZIP.
    """

    _validate_run_arguments(
        targets,
        config=config,
        sequence=sequence,
        invocation=invocation,
        entry=entry,
        preview=preview,
        archive_mtime=archive_mtime,
        output=output,
        force=force,
    )
    runtime_cwd = _runtime_cwd(cwd)
    runtime_output = _resolve_runtime_output(output, cwd=runtime_cwd)

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
        output=runtime_output,
        force=force,
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

"""Output path validation and ZIP archive writing."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import shutil
import tempfile
import zipfile

from ._builder_common import _is_link_like
from ._builder_models import ArchivePlan, BuildRequest
from .config import Config
from .errors import ConfigurationError, SelectionError


def _current_output_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _generated_output_filename(config: Config, request: BuildRequest) -> str:
    """Return one timestamp filename for Configuration or runtime directory output."""

    configured = config.output
    naming = configured if configured is not None and configured.generated else None
    parts: list[str] = []
    if naming is not None:
        if naming.prefix is not None:
            parts.append(naming.prefix)
    else:
        parts.append("dirpluck")
    parts.append(_current_output_timestamp())
    if request.sequence is not None:
        parts.append(str(request.sequence))
    if naming is not None and naming.suffix is not None:
        parts.append(naming.suffix)
    return "-".join(parts) + ".zip"


def _effective_output_is_generated(config: Config, request: BuildRequest) -> bool:
    if request.output is not None:
        return request.output.generated
    return config.output is not None and config.output.generated


def _resolve_output_path(config: Config, request: BuildRequest) -> tuple[Path, bool]:
    runtime_output = request.output
    if runtime_output is not None:
        if runtime_output.generated:
            candidate = runtime_output.path / _generated_output_filename(config, request)
        else:
            candidate = runtime_output.path
        overwrite = request.force
    else:
        output = config.output
        if output is None:
            raise ConfigurationError(
                f"{config.manifest}: the root Configuration must define "
                + "[output] or [output.timestamp], or the invocation must provide runtime output"
            )
        base = config.manifest.parent
        if output.generated:
            directory = Path(output.path)
            if not directory.is_absolute():
                directory = base / directory
            candidate = directory / _generated_output_filename(config, request)
            overwrite = request.force
        else:
            candidate = Path(output.path)
            if not candidate.is_absolute():
                candidate = base / candidate
            overwrite = request.force or output.overwrite

    if _is_link_like(candidate):
        raise SelectionError(
            f"output path must not be a symbolic link or Windows junction: {candidate}"
        )
    candidate = candidate.resolve(strict=False)
    if candidate.exists() and candidate.is_dir():
        raise SelectionError(f"output path is a directory: {candidate}")
    return candidate, overwrite


def _prepare_output(config: Config, request: BuildRequest) -> tuple[Path, bool]:  # pyright: ignore[reportUnusedFunction]
    """Resolve and validate the effective Output before archive planning begins."""

    if not isinstance(request.force, bool):
        raise SelectionError("output force must be a boolean")
    if request.sequence is not None:
        if (
            isinstance(request.sequence, bool)
            or not isinstance(request.sequence, int)
            or request.sequence < 1
        ):
            raise SelectionError("output sequence must be an integer greater than or equal to 1")
        if not _effective_output_is_generated(config, request):
            raise SelectionError("output sequence can only be used with timestamp output")

    output_path, overwrite = _resolve_output_path(config, request)
    if output_path.exists() and not overwrite:
        raise SelectionError(f"output archive already exists: {output_path}")
    return output_path, overwrite


def _zip_datetime(timestamp: datetime) -> tuple[int, int, int, int, int, int]:
    return (
        timestamp.year,
        timestamp.month,
        timestamp.day,
        timestamp.hour,
        timestamp.minute,
        timestamp.second,
    )


def _generated_zip_info(name: str, timestamp: datetime) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(filename=name, date_time=_zip_datetime(timestamp))
    if name.endswith("/"):
        info.external_attr = 0o40775 << 16
        info.external_attr |= 0x10
    else:
        info.external_attr = 0o600 << 16
    return info


def _write_source_with_mtime(
    archive: zipfile.ZipFile,
    source: Path,
    arcname: str,
    timestamp: datetime,
) -> None:
    info = zipfile.ZipInfo.from_file(
        source,
        arcname,
        strict_timestamps=False,
    )
    info.date_time = _zip_datetime(timestamp)
    info.compress_type = archive.compression
    with source.open("rb") as src, archive.open(info, "w") as dest:
        shutil.copyfileobj(src, dest, 1024 * 8)


def _write_archive(  # pyright: ignore[reportUnusedFunction]
    plan: ArchivePlan,
    output_path: Path,
    overwrite: bool,
    *,
    archive_mtime: datetime | None = None,
) -> Path:
    archive_entries = plan.entries
    output_resolved = output_path.resolve(strict=False)
    if any(path.resolve() == output_resolved for path in archive_entries.values()):
        raise SelectionError(f"output archive is selected as an input file: {output_path}")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SelectionError(f"cannot create output directory: {output_path.parent}") from exc

    try:
        temporary_directory = tempfile.TemporaryDirectory(
            prefix=f".{output_path.name}.",
            dir=output_path.parent,
        )
    except OSError as exc:
        raise SelectionError(
            f"cannot create temporary output directory: {output_path.parent}"
        ) from exc

    with temporary_directory as directory:
        temporary = Path(directory) / "archive.tmp"
        try:
            temporary.touch(mode=0o666, exist_ok=False)
        except OSError as exc:
            raise SelectionError(f"cannot create temporary output archive: {temporary}") from exc

        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            strict_timestamps=False,
        ) as archive:
            if archive_mtime is None:
                archive.writestr("README.md", plan.readme)
            else:
                archive.writestr(
                    _generated_zip_info("README.md", archive_mtime),
                    plan.readme,
                    compress_type=archive.compression,
                )
            for archive_directory in plan.empty_directories:
                directory_name = f"{archive_directory.rstrip('/')}/"
                if archive_mtime is None:
                    archive.writestr(directory_name, b"")
                else:
                    archive.writestr(
                        _generated_zip_info(directory_name, archive_mtime),
                        b"",
                        compress_type=archive.compression,
                    )
            for arcname, source in archive_entries.items():
                try:
                    if archive_mtime is None:
                        archive.write(source, arcname=arcname)
                    else:
                        _write_source_with_mtime(
                            archive,
                            source,
                            arcname,
                            archive_mtime,
                        )
                except OSError as exc:
                    raise SelectionError(f"cannot add selected file to archive: {source}") from exc

        if not overwrite and output_path.exists():
            raise SelectionError(f"output archive already exists: {output_path}")
        try:
            os.replace(temporary, output_path)
        except OSError as exc:
            raise SelectionError(f"cannot finalize output archive: {output_path}") from exc
        return output_path

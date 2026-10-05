"""Output path validation and ZIP archive writing."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import shutil
import tempfile
import zipfile

from ._filesystem import safe_is_link_like
from ._archive_payload import ArchivePayload
from ._output_models import NormalizedOutput
from .errors import SelectionError


def _current_output_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _generated_output_filename(output: NormalizedOutput) -> str:
    """Return one timestamp filename from a normalized output policy."""

    parts: list[str] = []
    if output.prefix is not None:
        parts.append(output.prefix)
    parts.append(_current_output_timestamp())
    if output.sequence is not None:
        parts.append(str(output.sequence))
    if output.suffix is not None:
        parts.append(output.suffix)
    return "-".join(parts) + ".zip"


def _resolve_output_path(output: NormalizedOutput) -> tuple[Path, bool]:
    candidate = (
        output.path / _generated_output_filename(output) if output.generated else output.path
    )
    if safe_is_link_like(candidate):
        raise SelectionError(
            f"output path must not be a symbolic link or Windows junction: {candidate}"
        )
    candidate = candidate.resolve(strict=False)
    if candidate.exists() and candidate.is_dir():
        raise SelectionError(f"output path is a directory: {candidate}")
    return candidate, output.overwrite


def prepare_output(output: NormalizedOutput) -> tuple[Path, bool]:
    """Resolve and validate one normalized output policy before writing."""

    output_path, overwrite = _resolve_output_path(output)
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


def _write_generated_entry(
    archive: zipfile.ZipFile,
    name: str,
    data: str | bytes,
    archive_mtime: datetime | None,
) -> None:
    try:
        if archive_mtime is None:
            archive.writestr(name, data)
        else:
            archive.writestr(
                _generated_zip_info(name, archive_mtime),
                data,
                compress_type=archive.compression,
            )
    except OSError as exc:
        raise SelectionError(f"cannot add generated entry to archive: {name}") from exc


def write_archive(
    payload: ArchivePayload,
    output_path: Path,
    overwrite: bool,
    *,
    archive_mtime: datetime | None = None,
) -> Path:
    archive_entries = payload.entries
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
            _write_generated_entry(archive, "README.md", payload.readme, archive_mtime)
            for archive_directory in payload.empty_directories:
                directory_name = f"{archive_directory.rstrip('/')}/"
                _write_generated_entry(archive, directory_name, b"", archive_mtime)
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

"""Archive-entry timestamp option parsing and resolution."""

from __future__ import annotations

from datetime import datetime
import re


ARCHIVE_MTIME_NOW = "now"
ARCHIVE_MTIME_ZIP_EPOCH = "zip-epoch"
ZIP_EPOCH = datetime(1980, 1, 1, 0, 0, 0)
ZIP_TIMESTAMP_MAX = datetime(2107, 12, 31, 23, 59, 59)
_TIMESTAMP_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$")
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S"


def validate_archive_mtime_spec(value: object) -> str:
    """Validate and return one CLI / Invocation archive-mtime specification."""

    if not isinstance(value, str) or not value:
        raise ValueError(
            "archive mtime must be 'now', 'zip-epoch', or a timestamp in "
            + "YYYY-MM-DDTHH:MM:SS form"
        )
    if value in {ARCHIVE_MTIME_NOW, ARCHIVE_MTIME_ZIP_EPOCH}:
        return value
    if not _TIMESTAMP_PATTERN.fullmatch(value):
        raise ValueError(
            "archive mtime must be 'now', 'zip-epoch', or a timestamp in "
            + "YYYY-MM-DDTHH:MM:SS form"
        )
    try:
        timestamp = datetime.strptime(value, _TIMESTAMP_FORMAT)
    except ValueError as exc:
        raise ValueError(f"invalid archive mtime timestamp: {value}") from exc
    _validate_zip_timestamp_range(timestamp)
    return value


def _validate_zip_timestamp_range(timestamp: datetime) -> None:
    if not ZIP_EPOCH <= timestamp <= ZIP_TIMESTAMP_MAX:
        raise ValueError(
            "archive mtime timestamp must be within "
            + "1980-01-01T00:00:00 through 2107-12-31T23:59:59"
        )


def _current_local_time() -> datetime:
    return datetime.now()


def resolve_archive_mtime(spec: str | None) -> datetime | None:
    """Resolve one validated specification to ZIP's two-second timestamp grid."""

    if spec is None:
        return None
    validated = validate_archive_mtime_spec(spec)
    if validated == ARCHIVE_MTIME_NOW:
        timestamp = _current_local_time().replace(microsecond=0)
        _validate_zip_timestamp_range(timestamp)
    elif validated == ARCHIVE_MTIME_ZIP_EPOCH:
        timestamp = ZIP_EPOCH
    else:
        timestamp = datetime.strptime(validated, _TIMESTAMP_FORMAT)

    return timestamp.replace(second=timestamp.second - (timestamp.second % 2), microsecond=0)

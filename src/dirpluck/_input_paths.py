"""Shared lexical path handling for dirpluck input documents."""

from __future__ import annotations

import glob
import os
from pathlib import Path, PurePosixPath, PureWindowsPath

from .errors import ConfigurationError


CONFIG_NAME = "default.dirpluck"
CONFIG_SUFFIX = ".dirpluck"


def validate_filesystem_location(path: str, where: str, *, label: str) -> str:
    """Validate one portable filesystem location without resolving it."""

    if not path:
        raise ConfigurationError(f"{where}: {label} must not be empty")
    if "\\" in path:
        raise ConfigurationError(
            f"{where}: backslashes are not allowed in filesystem locations; use '/' as the path separator"
        )
    if glob.has_magic(path):
        raise ConfigurationError(f"{where}: {label} must name one concrete path")

    pure = PurePosixPath(path)
    windows = PureWindowsPath(path)
    if (pure.is_absolute() or bool(windows.drive) or bool(windows.root)) and not Path(
        path
    ).is_absolute():
        raise ConfigurationError(
            f"{where}: absolute-root form is not supported by the host operating system"
        )
    return pure.as_posix()


def lexical_absolute_path(path: str | Path, *, cwd: Path | None = None) -> Path:
    """Anchor one path lexically without resolving symlinks or junctions."""

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (cwd or Path.cwd()) / candidate
    return Path(os.path.abspath(candidate))


def _config_reference(reference: str | None) -> str:
    if reference is None:
        return CONFIG_NAME
    if not isinstance(reference, str) or not reference.strip():
        raise ConfigurationError("configuration path must be a non-empty string")
    raw = reference.strip()
    if raw.endswith("/") or raw.rsplit("/", 1)[-1] in {".", ".."}:
        raise ConfigurationError("configuration path must name one Configuration file")
    path = validate_filesystem_location(raw, "--config", label="Configuration path")
    return path if path.endswith(CONFIG_SUFFIX) else path + CONFIG_SUFFIX


def resolve_config_path(reference: str | None = None, *, cwd: Path | None = None) -> Path:
    """Resolve one CLI Configuration reference to an existing lexical path."""

    candidate = lexical_absolute_path(_config_reference(reference), cwd=cwd)
    if not candidate.is_file():
        raise ConfigurationError(f"configuration file was not found: {candidate}")
    return candidate
